"""
Loop over structured sections (from parser.py) and call an LLM to extract entities from each one, using a JSON schema to force structured output.

Usage:
    python extract.py output.json --provider ollama > entities.json
    python extract.py output.json --provider gemini > entities.json
"""

import os
import json
import sys
import argparse

from dotenv import load_dotenv


load_dotenv()

# JSON schema for the extracted entities
UNIT_SCHEMA = {
    "type": "object",
    "properties": {
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "unit_id": {"type": "string"},
                    "associated_outdoor_unit": {"type": "string", "nullable": True},
                    "model_series": {"type": "string", "nullable": True},
                    "location": {"type": "string", "nullable": True},
                    "comment": {"type": "string", "nullable": True},
                },
                "required": ["unit_id"],
            },
        }
    },
    "required": ["units"],
}


def build_prompt(section: dict) -> str:
    """Frame the section with its heading context so the model isn't
    guessing what table/prose it's looking at."""
    heading_path = " > ".join(section.get("heading_path", [])) or "(no heading)"
    content_type = section.get("content_type", "prose")
 
    return (
        f"Document section: {heading_path}\n"
        f"Content type: {content_type}\n\n"
        f"{section['content']}\n\n"
        "Extract every distinct EQUIPMENT unit or POINT mentioned above as a "
        "structured entity.\n\n"
        "CRITICAL RULE for unit_id: use the leftmost or first-listed identifying "
        "name in each row exactly as written (e.g. an equipment tag like "
        "'H-LL-FCU-L2.W1', or a point name like 'Zone Temperature', 'CO2 Sensor', "
        "'Unit Enable'). NEVER use a sensor model number, part number, or "
        "manufacturer code (e.g. 'Belimo 22-RTM-19-1') as the unit_id. If a model "
        "number appears in the row, it belongs in comment, not unit_id.\n\n"
        "CRITICAL RULE against fabrication: only put a value in location if that "
        "exact location is stated in the row or clearly implied by the immediate "
        "row context. NEVER invent a plausible-sounding location, zone name, or "
        "floor reference that is not explicitly present in the source text. If no "
        "location is given, use the JSON value null.\n\n"
        "Do NOT extract rows from this table as units if the table is describing "
        "CONDITIONAL LOGIC rather than physical equipment or points. Signs a table "
        "is conditional logic: its column headers are conditions or states (e.g. "
        "'Occupancy', 'Mode', 'Status', 'Count', a comparison like '>5'), or its "
        "rows describe combinations of inputs and outputs rather than naming a "
        "device or point. If the section is describing this kind of logic table, "
        "return an empty units array instead of guessing.\n\n"
        "Skip any row that is a section divider or repeats a floor/level label "
        "in every column rather than describing a real unit. "
        "If a field genuinely isn't present, use the JSON value null, never the "
        "string \"null\". "
        "Respond with ONLY the JSON object, no other text."
    )


def _call_ollama(prompt, schema=UNIT_SCHEMA) -> str:
    import ollama

    model = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=schema,  # forces schema-conformant JSON output
        options={"temperature": 0, "repeat_penalty": 1.3, "num_predict": 4000},
    )
    return response["message"]["content"]


def _call_gemini(prompt, schema=UNIT_SCHEMA) -> str:
    from google import genai
    from google.genai import types

    model = "gemini-3.5-flash-lite"
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )
    )
    return response.text


PROVIDERS = {
    "ollama": _call_ollama,
    "gemini": _call_gemini,
}


def merge_split_sections(sections: list) -> list:
    """PDF tables that span a page break get parsed as two separate
    chunks sharing the same section_id, each carrying its own repeated
    header row. Merge chunks with the same section_id into one,
    stripping the header line from every chunk after the first so it
    isn't duplicated in the combined content."""
    merged = {}
    order = []
    for s in sections:
        sid = s.get("section_id")
        if sid not in merged:
            merged[sid] = dict(s)
            order.append(sid)
        else:
            content = s["content"]
            lines = content.split("\n")
            # drop the header row + separator row (first 2 lines) from
            # every chunk after the first, if they match a markdown table
            if len(lines) > 2 and lines[0].strip().startswith("|") and set(lines[1].strip()) <= set("|-: "):
                content = "\n".join(lines[2:])
            merged[sid]["content"] = merged[sid]["content"].rstrip() + "\n" + content.lstrip()
    return [merged[sid] for sid in order]
 
 
def extract_from_section(section: dict, provider: str) -> dict:
    """Call the LLM for a single section. Returns a dict with the parsed
    entities plus the section's traceability metadata, or an error entry
    if parsing failed. Retries once on a JSON parse failure before
    giving up on the section."""
    
    prompt = build_prompt(section)
    call_fn = PROVIDERS[provider]
    raw = None
 
    try:
        raw = call_fn(prompt, UNIT_SCHEMA)
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        try:
            raw = call_fn(prompt, UNIT_SCHEMA)
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            return {
                "section_id": section["section_id"],
                "heading_path": section["heading_path"],
                "error": f"JSON parse failure: {e}",
                "raw_output": raw,
                "units": [],
            }
    except Exception as e:
        return {
            "section_id": section["section_id"],
            "heading_path": section["heading_path"],
            "error": f"LLM call failed: {e}",
            "units": [],
        }
 
    return {
        "section_id": section["section_id"],
        "heading_path": section["heading_path"],
        "source": section.get("source", {}),
        "units": parsed.get("units", []),
    }
 
 
def extract_all(sections: list, provider: str, only_tables: bool = True) -> list:
    """Run extraction across all sections. By default, skips pure-prose
    sections that are unlikely to contain tabular entities. Flip
    only_tables=False if entities can also appear in prose. Sections
    split across a page break (sharing a section_id) are merged first
    so each table is seen whole, in a single call."""
    table_sections = [
        s for s in sections
        if not only_tables or s.get("content_type") in ("table", "table_html")
    ]
    table_sections = merge_split_sections(table_sections)
    results = []
    for section in table_sections:
        results.append(extract_from_section(section, provider))
    return results
 
 
def merge_units(results: list) -> list:
    """Flatten per-section results into one list, tagging each unit with
    where it came from for traceability. Also does a light dedupe on
    unit_id in case the same unit appears in overlapping sections."""
    merged = []
    seen_ids = set()
    for r in results:
        if r.get("error"):
            continue
        for unit in r["units"]:
            unit = {k: (None if v == "null" else v) for k, v in unit.items()}
            unit_id = unit.get("unit_id")
            key = (unit_id, r["section_id"])
            if key in seen_ids:
                continue
            seen_ids.add(key)
            merged.append({
                **unit,
                "_section_id": r["section_id"],
                "_heading_path": r["heading_path"],
            })
    return merged
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sections_path", help="Path to sections.json")
    parser.add_argument(
        "--provider",
        choices=PROVIDERS.keys(),
        default=os.environ.get("PROVIDER", "ollama"),
        help="Which LLM backend to use (default: $PROVIDER env var, or 'ollama')",
    )
    args = parser.parse_args()
 
    with open(args.sections_path, "r", encoding="utf-8") as f:
        sections = json.load(f)
 
    print(f"Using provider: {args.provider}", file=sys.stderr)
    results = extract_all(sections, provider=args.provider, only_tables=True)
 
    failures = [r for r in results if r.get("error")]
    if failures:
        print(f"Warning: {len(failures)} section(s) failed extraction:", file=sys.stderr)
        for f_ in failures:
            print(f"  - {f_['section_id']}: {f_['error']}", file=sys.stderr)
 
    all_units = merge_units(results)
    print(json.dumps(all_units, indent=2, ensure_ascii=False))

    model_tag = os.environ.get("OLLAMA_MODEL", "default").replace(":", "-")
    provider_folder = "qwen" if "qwen" in model_tag else ("llama" if "llama" in model_tag else args.provider)
    out_dir = os.path.join("results", provider_folder)
    os.makedirs(out_dir, exist_ok=True)
    out_name = f"entities_{args.provider}_{model_tag}.json" if args.provider == "ollama" else f"entities_{args.provider}.json"
    out_path = os.path.join(out_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_units, f, indent=4)