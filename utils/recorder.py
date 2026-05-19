"""LLM call recording helpers: JSONL and SQLite options for testing.

Usage:
  - Set env `PDFREE_RECORD_LLM` to one of: off (default), jsonl, sqlite, both
  - JSONL file: `pdf_backend/outputs/llm_calls.jsonl`
  - SQLite file: `pdf_backend/outputs/llm_calls.db`

This is intentionally simple and safe for local testing.
"""

from __future__ import annotations

import os
import json
import time
import sqlite3
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_JSONL = os.path.join("pdf_backend", "outputs", "llm_calls.jsonl")
DEFAULT_DB = os.path.join("pdf_backend", "outputs", "llm_calls.db")


def _record_jsonl(prompt: str, response: str, metadata: dict | None, path: str = DEFAULT_JSONL) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    entry = {
        "ts": time.time(),
        "prompt": prompt,
        "response": response,
        "metadata": metadata or {},
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write JSONL recorder: {e}")


def _ensure_db(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL,
                prompt TEXT,
                response TEXT,
                metadata TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _record_sqlite(prompt: str, response: str, metadata: dict | None, path: str = DEFAULT_DB) -> None:
    _ensure_db(path)
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO llm_calls (ts, prompt, response, metadata) VALUES (?, ?, ?, ?)",
            (time.time(), prompt, response, json.dumps(
                metadata or {}, ensure_ascii=False)),
        )
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to write SQLite recorder: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def record_llm_call(prompt: str, response: str, metadata: dict | None = None) -> None:
    """Record an LLM interaction depending on `PDFREE_RECORD_LLM`.

    Supported values: off (default), jsonl, sqlite, both
    """
    mode = os.getenv("PDFREE_RECORD_LLM", "off").strip().lower()
    if mode == "off" or mode == "false" or mode == "0":
        return

    if mode in ("jsonl", "both"):
        _record_jsonl(prompt, response, metadata)

    if mode in ("sqlite", "both"):
        _record_sqlite(prompt, response, metadata)
