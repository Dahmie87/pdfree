#!/usr/bin/env python
"""Standalone CLI for testing book generation."""

import sys
from pathlib import Path
from dotenv import load_dotenv
from agent.book_agent import BookGenerationAgent

# Load environment variables from .env
load_dotenv()


def main():
    """Run agent from CLI."""
    if len(sys.argv) < 2:
        print("Usage: python cli.py 'Your book prompt'")
        print("\nExample:")
        print("  python cli.py 'Write a book about blockchain technology'")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    print("\n" + "="*50)
    print("🚀 PDFree Book Generation Agent")
    print("="*50 + "\n")

    agent = BookGenerationAgent()
    pdf_bytes, title = agent.generate_pdf_book(prompt)

    # Save to file
    filename = f"book_{title.replace(' ', '_')[:30]}.pdf"
    output_path = Path.cwd() / filename

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"\n✅ Success! PDF saved to: {output_path}")
    print(f"   File size: {len(pdf_bytes) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
