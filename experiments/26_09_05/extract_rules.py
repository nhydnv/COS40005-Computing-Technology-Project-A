"""
Call Groq (OpenAI-compatible endpoint) to extract control rules from
structured sections (from parser.py), identifying the independent and
dependent variables involved in each rule.

Two modes:
  --mode whole         (default) Concatenate every section into one prompt
                       and extract rules in a single LLM call. Best when
                       rules are stated in prose and may reference
                       definitions from other sections/tables.
  --mode per-section   Run extraction section-by-section, then merge.
                       Cheaper and avoids context-length limits on very
                       large documents, but a rule split across two
                       sections may come out incomplete or get missed.

Usage:
    python extract_rules.py output.json > rules.json
    python extract_rules.py output.json --mode per-section > rules.json
"""

import os
import copy
import json
import sys
import argparse

from dotenv import load_dotenv


load_dotenv()

# JSON schema for the extracted control rules
RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rule_id": {"type": "string"},
                    "description": {
                        "type": "string",
                        "description": "Plain-language restatement of the rule.",
                    },
                    "independent_variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Conditions/inputs that trigger or drive the rule (the 'if/when' side).",
                    },
                    "dependent_variables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Outcomes/outputs controlled by the rule (the 'then' side).",
                    },
                    "section_id": {
                        "type": "string",
                        "description": "The section number this rule was found under (e.g. '1.2.3'), exactly as labeled above it.",
                    },
                },
                "required": [
                    "rule_id",
                    "description",
                    "independent_variables",
                    "dependent_variables",
                    "section_id",
                ],
            },
        }
    },
    "required": ["rules"],
}


EXTRACTION_INSTRUCTION = (
    "Extract every distinct control rule mentioned above. "
    "For each rule, identify the relevant components as independent and "
    "dependent variables. "
    "For section_id, copy the exact section number labeled above the text "
    "the rule appeared in (e.g. '1.2.3') — do not paraphrase it. "
    "Respond with ONLY the JSON object, no other text."
)


def build_prompt_for_section(section: dict) -> str:
    """Frame a single section with its section number and heading."""
    heading_path = " > ".join(section.get("heading_path", [])) or "(no heading)"
    content_type = section.get("content_type", "prose")

    return (
        f"Section {section['section_id']}: {heading_path}\n"
        f"Content type: {content_type}\n\n"
        f"{section['content']}\n\n"
        f"{EXTRACTION_INSTRUCTION}"
    )


def build_prompt_for_document(sections: list) -> str:
    """Concatenate every section into one prompt, each labeled with its
    section number, so the model sees the whole document at once and can
    connect rules to variables defined elsewhere."""
    parts = []
    for section in sections:
        heading_path = " > ".join(section.get("heading_path", [])) or "(no heading)"
        content_type = section.get("content_type", "prose")
        parts.append(
            f"--- Section {section['section_id']}: {heading_path} ({content_type}) ---\n{section['content']}"
        )
    document_text = "\n\n".join(parts)

    return f"{document_text}\n\n{EXTRACTION_INSTRUCTION}"


def _to_strict_json_schema(schema: dict) -> dict:
    """Groq's 'strict' structured-output mode requires plain JSON Schema:
    - "additionalProperties": false on every object, at every nesting level
    - no OpenAPI-style "nullable": true (use ["type", "null"] instead)
    - every property listed in "required" (optionality is expressed via
      allowing null, not by omission)

    This walks the schema and rewrites it to satisfy those rules.
    """
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


def call_groq(prompt: str, schema: dict = RULE_SCHEMA) -> str:
    """Call an OpenAI-style model hosted on Groq. Groq exposes an
    OpenAI-compatible /v1 endpoint, so we point the standard `openai`
    SDK at Groq's base_url instead of using a separate client.
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
                "name": "rule_extraction",
                "schema": strict_schema,
                "strict": True,
            },
        },
    )
    return response.choices[0].message.content


def extract_from_section(section: dict) -> dict:
    """Call Groq for a single section. Returns a dict with the parsed
    rules plus traceability metadata, or an error entry if parsing failed."""
    prompt = build_prompt_for_section(section)
    raw = None

    try:
        raw = call_groq(prompt, RULE_SCHEMA)
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "section_id": section["section_id"],
            "heading_path": section["heading_path"],
            "error": f"JSON parse failure: {e}",
            "raw_output": raw,
            "rules": [],
        }
    except Exception as e:
        return {
            "section_id": section["section_id"],
            "heading_path": section["heading_path"],
            "error": f"LLM call failed: {e}",
            "rules": [],
        }

    return {
        "section_id": section["section_id"],
        "heading_path": section["heading_path"],
        "source": section.get("source", {}),
        "rules": parsed.get("rules", []),
    }


def extract_per_section(sections: list) -> list:
    """Run extraction section-by-section, then flatten + tag results."""
    results = [extract_from_section(s) for s in sections]

    failures = [r for r in results if r.get("error")]
    if failures:
        print(f"Warning: {len(failures)} section(s) failed extraction:", file=sys.stderr)
        for f_ in failures:
            print(f"  - {f_['section_id']}: {f_['error']}", file=sys.stderr)

    merged = []
    for r in results:
        if r.get("error"):
            continue
        for rule in r["rules"]:
            rule = dict(rule)
            rule["section_id"] = r["section_id"]  # trust the known section, not the model's copy of it
            merged.append(rule)
    return merged


def extract_whole_document(sections: list) -> list:
    """Run extraction once over the entire concatenated document. The
    model is asked to report the section_id each rule came from directly
    (each chunk in the prompt is labeled with its section number)."""
    prompt = build_prompt_for_document(sections)
    raw = None

    try:
        raw = call_groq(prompt, RULE_SCHEMA)
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: JSON parse failure: {e}", file=sys.stderr)
        print(f"Raw output was:\n{raw}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error: LLM call failed: {e}", file=sys.stderr)
        return []

    return parsed.get("rules", [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sections_path", help="Path to sections.json")
    parser.add_argument(
        "--mode",
        choices=["whole", "per-section"],
        default=os.environ.get("MODE", "whole"),
        help="Extract from the whole document in one call, or section-by-section (default: whole)",
    )
    args = parser.parse_args()

    with open(args.sections_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    print(f"Using mode: {args.mode}", file=sys.stderr)

    if args.mode == "whole":
        all_rules = extract_whole_document(sections)
    else:
        all_rules = extract_per_section(sections)

    print(json.dumps(all_rules, indent=2, ensure_ascii=False))
    with open(f"rules_{args.mode}.json", "w", encoding="utf-8") as f:
        json.dump(all_rules, f, indent=4)