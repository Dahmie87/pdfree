"""LLM call recording helpers: JSONL and SQLite options.

Usage:
    - Set env PDFREE_RECORD_LLM to one of: off, jsonl, sqlite, both, all
    - Default mode is both so local runs are recorded without extra setup
    - JSONL file defaults to <repo>/pdf_backend/outputs/llm_calls.jsonl
    - SQLite file defaults to <repo>/pdf_backend/outputs/llm_calls.db

Optional overrides:
    - PDFREE_RECORD_JSONL_PATH
    - PDFREE_RECORD_DB_PATH
"""

from __future__ import annotations

import os
import json
import time
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_JSONL = str(_BASE_DIR / "outputs" / "llm_calls.jsonl")
DEFAULT_DB = str(_BASE_DIR / "outputs" / "llm_calls.db")


def _ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _resolve_record_paths() -> tuple[str, str]:
    jsonl_path = os.getenv("PDFREE_RECORD_JSONL_PATH", DEFAULT_JSONL).strip()
    db_path = os.getenv("PDFREE_RECORD_DB_PATH", DEFAULT_DB).strip()
    return jsonl_path, db_path


def _record_jsonl(prompt: str, response: str, metadata: dict | None, path: str) -> None:
    _ensure_parent_dir(path)
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
    _ensure_parent_dir(path)
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


def _record_sqlite(prompt: str, response: str, metadata: dict | None, path: str) -> None:
    _ensure_db(path)
    conn = None
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
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def record_llm_call(prompt: str, response: str, metadata: dict | None = None) -> None:
    """Record an LLM interaction depending on PDFREE_RECORD_LLM.

    Supported values: off, jsonl, sqlite, both, all
    """
    mode = os.getenv("PDFREE_RECORD_LLM", "both").strip().lower()
    if mode == "off" or mode == "false" or mode == "0":
        return

    if not isinstance(prompt, str):
        prompt = str(prompt)
    if not isinstance(response, str):
        response = str(response)

    jsonl_path, db_path = _resolve_record_paths()

    if mode == "all":
        mode = "both"

    if mode in ("jsonl", "both"):
        _record_jsonl(prompt, response, metadata, path=jsonl_path)

    if mode in ("sqlite", "both"):
        _record_sqlite(prompt, response, metadata, path=db_path)

    if mode not in ("jsonl", "sqlite", "both"):
        logger.warning(
            "Unknown PDFREE_RECORD_LLM mode '%s'; expected off/jsonl/sqlite/both/all",
            mode,
        )
