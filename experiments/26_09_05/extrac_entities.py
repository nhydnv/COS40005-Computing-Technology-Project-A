"""
Loop over structured sections (from parser.py) and call an LLM to extract entities from each one, using a JSON schema to force structured output.

Usage:
    python extract.py output.json --provider ollama > entities_ollama.json
    python extract.py output.json --provider gemini > entities_gemini.json
    python extract.py output.json --provider groq > entities_groq.json
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
        "Extract every distinct equipment unit mentioned above as a structured "
        "entity. Skip any row that is a section divider or repeats a floor/level "
        "label in every column rather than describing a real unit. "
        "If a field isn't present, use null. "
        "Respond with ONLY the JSON object, no other text."
    )


def _call_ollama(prompt, schema=UNIT_SCHEMA) -> str:
    import ollama

    model = "llama3.2:1b"

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=schema,  # forces schema-conformant JSON output
        options={"temperature": 0},
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


def _to_strict_json_schema(schema: dict) -> dict:
    """Groq (and OpenAI) 'strict' structured-output mode enforces plain
    JSON Schema, which is stricter than what UNIT_SCHEMA was written for:
 
    - every object needs "additionalProperties": false, at every nesting
      level, not just the root
    - "nullable": true (an OpenAPI-ism, not real JSON Schema) doesn't work;
      a nullable field has to be typed as e.g. ["string", "null"]
    - in strict mode every property has to be listed in "required" (you
      express "optional" by allowing null, not by omitting it)
 
    This walks the schema and rewrites it to satisfy those rules, so
    UNIT_SCHEMA itself doesn't have to be duplicated or hand-edited for
    Gemini vs. Groq.
    """
    import copy
 
    schema = copy.deepcopy(schema)
 
    def fix(node):
        if not isinstance(node, dict):
            return node
        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node["properties"].keys())
            for value in node["properties"].values():
                fix(value)
        if node.pop("nullable", False):
            t = node.get("type")
            if isinstance(t, list):
                if "null" not in t:
                    t.append("null")
            elif t is not None:
                node["type"] = [t, "null"]
        if node.get("type") == "array" and "items" in node:
            fix(node["items"])
        return node
 
    return fix(schema)
 
 
def _call_groq(prompt, schema=UNIT_SCHEMA) -> str:
    """Call an OpenAI-style model hosted on Groq. Groq exposes an
    OpenAI-compatible /v1 endpoint, so we just point the standard
    `openai` SDK at Groq's base_url instead of using a separate client.
 
    Model choice: "openai/gpt-oss-120b" is OpenAI's open-weight model
    running on Groq's hardware.
    """
    from openai import OpenAI
 
    model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
 
    strict_schema = _to_strict_json_schema(schema)
 
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "unit_extraction",
                "schema": strict_schema,
                "strict": True,
            },
        },
    )
    return response.choices[0].message.content


PROVIDERS = {
    "ollama": _call_ollama,
    "gemini": _call_gemini,
    "groq": _call_groq
}
 
 
def extract_from_section(section: dict, provider: str) -> dict:
    """Call the LLM for a single section. Returns a dict with the parsed
    entities plus the section's traceability metadata, or an error entry
    if parsing failed."""
    
    prompt = build_prompt(section)
    call_fn = PROVIDERS[provider]
    raw = None
 
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
    only_tables=False if entities can also appear in prose."""
    results = []
    for section in sections:
        if only_tables and section.get("content_type") not in ("table", "table_html"):
            continue
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
    with open(f"entities_{args.provider}.json", "w", encoding="utf-8") as f:
        json.dump(all_units, f, indent=4)