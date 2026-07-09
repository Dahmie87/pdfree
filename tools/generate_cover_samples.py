"""Generate sample PDFs for each cover design.
Creates 5 samples per design in `pdf_backend/samples/`.
Run from repo root:

    python -m pdf_backend.tools.generate_cover_samples

This script uses the existing `PDFGenerator` (no LLM calls).
"""

import os
from pathlib import Path
from generation.pdf_generator import PDFGenerator

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "samples"
DESIGNS = ["split", "frame", "stack", "bleed", "arch"]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gen = PDFGenerator()

    for design in DESIGNS:
        for i in range(1, 6):
            title = f"Test {design.capitalize()} {i} — A Very Long Title To Exercise Wrapping And Layout"
            content = ("This is sample content used to build a PDF for testing purposes.\n\n" * 40).strip()
            filename = OUTPUT_DIR / f"cover_{design}_{i}.pdf"
            print(f"Generating: {filename}")
            try:
                pdf_bytes = gen.generate_pdf(title=title, content=content, author="Tester", writing_mode="casual", cover_design=design)
                with open(filename, "wb") as f:
                    f.write(pdf_bytes)
            except Exception as e:
                print(f"Failed to generate {filename}: {e}")

    print("Done. Samples written to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
