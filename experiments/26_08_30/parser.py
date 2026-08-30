"""
Parse a PDF using Docling and convert it into a list of structured, self-contained sections.

Each section includes:
    - section_id       : the heading number if detected (e.g. "1.1.3"), else a generated id
    - heading_path     : list of ancestor headings, root -> leaf
    - heading_text     : the section's own heading text
    - content_type     : "table" | "prose" | "mixed"
    - content          : markdown string
    - source           : {"page_no": ..., "doc_name": ...} for traceability

Usage:
    python parser.py docs/air_conditioning.pdf > output.json
"""

import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DocItemLabel, SectionHeaderItem, TableItem, TextItem


OUTPUT_PATH = Path("./output.json")
HEADING_NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+(.*)$")


@dataclass
class Section:
    """
    Each section includes:
        - section_id       : the heading number if detected (e.g. "1.1.3"), else a generated id
        - heading_path     : list of ancestor headings, root -> leaf
        - heading_text     : the section's own heading text
        - content_type     : "table" | "prose" | "mixed"
        - content          : markdown string
        - source           : {"page_no": ..., "doc_name": ...} for traceability
    """
    section_id: str
    heading_path: list = field(default_factory=list)
    heading_text: str = ""
    content_type: str = "prose"
    content: str = ""
    source: dict = field(default_factory=dict)


def is_real_heading(text: str) -> bool:
    return bool(HEADING_NUM_RE.match(text.strip()))


def parse_heading(text: str, fallback_id: str):
    """Return (section_id, clean_heading_text). Falls back to a generated id
    if the heading has no leading numbering."""
    match = HEADING_NUM_RE.match(text)
    if match:
        return match.group(1), match.group(2).strip()
    return fallback_id, text.strip()


def convert(pdf_path: str) -> list:
    if not OUTPUT_PATH.is_file():
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = result.document

        sections = []
        heading_stack = []
        current = None
        auto_id_counter = 0

        def push_current():
            if current is not None and current.content.strip():
                sections.append(current)

        for item, level in doc.iterate_items():
            label = getattr(item, "label", None)
            is_heading_type = isinstance(item, SectionHeaderItem) or label == DocItemLabel.SECTION_HEADER

            # Heading: start a new section
            if is_heading_type and is_real_heading(item.text):
                push_current()
                auto_id_counter += 1
                section_id, heading_text = parse_heading(item.text, f"auto-{auto_id_counter}")

                # Maintain heading hierarchy by nesting level
                heading_stack = [h for h in heading_stack if h[0] < level]
                heading_stack.append((level, section_id, heading_text))
                heading_path = [h[2] for h in heading_stack]

                current = Section(
                    section_id=section_id,
                    heading_path=heading_path,
                    heading_text=heading_text,
                    source={
                        "page_no": [prov.page_no for prov in item.prov] if item.prov else [],
                        "doc_name": Path(pdf_path).name
                    },
                )

                continue

            if current is None:
                auto_id_counter += 1
                current = Section(
                    section_id=f"auto-{auto_id_counter}",
                    heading_path=[],
                    heading_text="",
                    source={
                        "page_no": [prov.page_no for prov in item.prov] if item.prov else [],
                        "doc_name": Path(pdf_path).name
                    },
                )

            # Table content
            if isinstance(item, TableItem):
                if current.content.strip():
                    
                    # Don't merge unrelated prose + table into one blob,
                    # push prose as its own section, start a fresh one for the table
                    push_current()
                    current = Section(
                        section_id=current.section_id,
                        heading_path=current.heading_path,
                        heading_text=current.heading_text,
                        source=current.source,
                    )

                current.content_type = "table"
                current.content = item.export_to_markdown(doc)
                push_current()
                current = Section(
                    section_id=current.section_id,
                    heading_path=current.heading_path,
                    heading_text=current.heading_text,
                    source=current.source,
                )
                continue

            # Prose content
            if isinstance(item, TextItem) and item.text.strip():
                text = item.text.strip()
                if current.content:
                    current.content += "\n\n" + text
                else:
                    current.content = text
                current.content_type = "prose"

        push_current()
        sections = [asdict(s) for s in sections]

        # Open a file in write mode ('w') and save the data
        with open(OUTPUT_PATH, "w") as f:
            json.dump(sections, f, indent=4)

        return sections
    
    else:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            sections = json.load(f)
        return sections


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage python parser.py path/to/file/pdf", file=sys.stderr)
        sys.exit(1)

    convert(sys.argv[1])