"""Regenerate PDFs from saved LLM case response files.

Usage:
  python regenerate_from_saved.py [base_dir]

If no `base_dir` is provided, the script will use the most recent
folder under `outputs/llm_cases/`.
"""
from __future__ import annotations
from generation.pdf_generator import PDFGenerator
import json
import sys
import os
from typing import Optional

# FIX sys.path IMMEDIATELY, before anything else
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


# SECOND: Import generation (now sys.path is fixed)


def _latest_llm_cases_dir(root: str) -> Optional[str]:
    if not os.path.isdir(root):
        return None
    entries = [
        os.path.join(root, p) for p in os.listdir(root)
        if os.path.isdir(os.path.join(root, p))
    ]
    if not entries:
        return None
    return sorted(entries)[-1]


def regenerate_from(base_dir: str) -> None:
    base_dir = os.path.abspath(base_dir)
    if not os.path.isdir(base_dir):
        raise SystemExit(f"Base directory not found: {base_dir}")

    pdf_gen = PDFGenerator()
    summary = []

    for entry in sorted(os.listdir(base_dir)):
        case_dir = os.path.join(base_dir, entry)
        if not os.path.isdir(case_dir):
            continue

        meta_path = os.path.join(case_dir, "metadata.json")
        content_path = os.path.join(case_dir, "content.txt")

        if not os.path.exists(content_path):
            summary.append((entry, "missing content", None))
            continue

        # Load metadata if present
        title = entry
        author = "AI Generated"
        try:
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                title = meta.get("title") or meta.get("name") or title
                author = meta.get("author", author)
        except Exception:
            pass

        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            pdf_bytes = pdf_gen.generate_pdf(
                title=title, content=content, author=author)
            out_pdf = os.path.join(case_dir, "book.pdf")
            with open(out_pdf, "wb") as pf:
                pf.write(pdf_bytes)
            summary.append((entry, "ok", out_pdf))
        except Exception as exc:  # pragma: no cover - runtime errors
            summary.append((entry, f"error: {exc}", None))

    # Print summary
    for case, status, path in summary:
        if path:
            print(f"{case}: {status} -> {path}")
        else:
            print(f"{case}: {status}")


def main():
    # Determine default base_dir
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    llm_root = os.path.join(repo_root, "outputs", "llm_cases")

    base_dir = None
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = _latest_llm_cases_dir(llm_root)

    if not base_dir:
        raise SystemExit(f"No llm_cases directory found under {llm_root}")

    print(f"Regenerating PDFs from: {base_dir}")
    regenerate_from(base_dir)


if __name__ == "__main__":
    main()
