from pathlib import Path

import ollama
from docling.document_converter import DocumentConverter


PDF_PATH = Path("../docs/air_conditioning.pdf")

converter = DocumentConverter()
result = converter.convert(PDF_PATH)
doc = result.document

# Export document to markdown
print("Writing PDF to markdown...")
markdown_text = doc.export_to_markdown()

# Save so that we can inspect the content that was parsed
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)

response = ollama.chat(
    model="llama3.2:1b",
    messages=[
        {
            "role": "user",
            "content": f"Give me a summary of the air conditioning units and how they are connected from the following function descriptions of the Late Lab building.\n\nFunctional description: {markdown_text}"
        }
    ]
)

content = response['message']['content']

# Save the model's response
with open("summary.txt", "w", encoding="utf-8") as f:
    f.write(content)