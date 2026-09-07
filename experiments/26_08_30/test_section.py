"""
Quick test: run extraction on just sections 1.1.3 and 1.1.4 (the two
known-hard tables) instead of the whole document. Use this to check
whether a new model/config is actually worth a full run before
committing 30-60+ minutes to it.

Usage:
    set OLLAMA_MODEL=qwen3:8b
    python test_section.py output.json
"""

import json
import sys
import os

from extract import extract_from_section, merge_units, merge_split_sections

TARGET_SECTIONS = {"1.1.3", "1.1.4"}

if __name__ == "__main__":
    sections_path = sys.argv[1] if len(sys.argv) > 1 else "output.json"

    with open(sections_path, "r", encoding="utf-8") as f:
        all_sections = json.load(f)

    raw_sections = [s for s in all_sections if s.get("section_id") in TARGET_SECTIONS]
    sections = merge_split_sections(raw_sections)
    print(f"Found {len(raw_sections)} raw chunk(s), merged into {len(sections)} section(s): {[s['section_id'] for s in sections]}", file=sys.stderr)

    results = []
    for section in sections:
        print(f"Processing {section['section_id']}...", file=sys.stderr)
        result = extract_from_section(section, provider="ollama")
        results.append(result)
        if result.get("error"):
            print(f"  FAILED: {result['error']}", file=sys.stderr)
        else:
            print(f"  OK - {len(result['units'])} units extracted", file=sys.stderr)

    all_units = merge_units(results)
    print(json.dumps(all_units, indent=2, ensure_ascii=False))

    model_tag = os.environ.get("OLLAMA_MODEL", "default").replace(":", "-")
    out_dir = os.path.join("results", "qwen")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"test_1.1.3_1.1.4_merged_{model_tag}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_units, f, indent=4)
    print(f"\nSaved to {out_path}", file=sys.stderr)