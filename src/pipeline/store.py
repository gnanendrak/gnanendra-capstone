"""W4 REFERENCE — src/pipeline/store.py

Extends the W2 SQLite store with two new columns:
  • cost_usd  REAL    — actual per-call cost from response.usage × rates
  • model     TEXT    — which model produced the answer

Adds ensure_schema() that runs idempotent ALTER TABLE migrations so a cohort
member can rerun without breaking an existing answers.db.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# ─── Schema (idempotent) ────────────────────────────────────────────────────
_BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT NOT NULL,
    content         TEXT NOT NULL,
    retries         INTEGER DEFAULT 0,
    cost_usd        REAL DEFAULT 0.0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    golden_id        TEXT NOT NULL,
    question         TEXT NOT NULL,
    candidate_answer TEXT NOT NULL,
    ideal_answer     TEXT NOT NULL,
    candidate_model  TEXT NOT NULL,
    judge_model      TEXT NOT NULL,
    accuracy         INTEGER NOT NULL,
    groundedness     INTEGER NOT NULL,
    format           INTEGER NOT NULL,
    reasoning        TEXT NOT NULL,
    eval_run_label   TEXT DEFAULT 'eval-run-001',
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

_EXPECTED_EVAL_RUNS_SCHEMA = [
    ("id", "INTEGER", 0, None),
    ("golden_id", "TEXT", 1, None),
    ("question", "TEXT", 1, None),
    ("candidate_answer", "TEXT", 1, None),
    ("ideal_answer", "TEXT", 1, None),
    ("candidate_model", "TEXT", 1, None),
    ("judge_model", "TEXT", 1, None),
    ("accuracy", "INTEGER", 1, None),
    ("groundedness", "INTEGER", 1, None),
    ("format", "INTEGER", 1, None),
    ("reasoning", "TEXT", 1, None),
    ("eval_run_label", "TEXT", 0, "'eval-run-001'"),
    ("created_at", "TEXT", 0, "CURRENT_TIMESTAMP"),
]

# Columns added in W4. Each entry: (column_name, column_def).
# Applied via ALTER TABLE only if missing — so the migration is safe to rerun.
_W4_NEW_COLUMNS = [
    ("model", "TEXT"),
    ("confidence", "REAL"),
    ("sources_json", "TEXT"),  # list[str] stored as JSON
    ("schema_version", "TEXT DEFAULT 'v1'"),
]


def ensure_schema(db_path: str | Path) -> None:
    """Create answers table if missing, then add any missing W4 columns.

    Safe to call on an empty file, on a W2/W3 db, or on a fully-migrated db.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_BASE_SCHEMA)
        eval_runs_schema = [
            (row[1], row[2], row[3], row[4])
            for row in conn.execute("PRAGMA table_info(eval_runs)").fetchall()
        ]
        if eval_runs_schema != _EXPECTED_EVAL_RUNS_SCHEMA:
            conn.execute("DROP TABLE IF EXISTS eval_runs")
            conn.execute("""
                CREATE TABLE eval_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    golden_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    candidate_answer TEXT NOT NULL,
                    ideal_answer TEXT NOT NULL,
                    candidate_model TEXT NOT NULL,
                    judge_model TEXT NOT NULL,
                    accuracy INTEGER NOT NULL,
                    groundedness INTEGER NOT NULL,
                    format INTEGER NOT NULL,
                    reasoning TEXT NOT NULL,
                    eval_run_label TEXT DEFAULT 'eval-run-001',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """)
        # Read current columns.
        cur = conn.execute("PRAGMA table_info(answers)")
        existing = {row[1] for row in cur.fetchall()}

        for col_name, col_def in _W4_NEW_COLUMNS:
            if col_name not in existing:
                conn.execute(f"ALTER TABLE answers ADD COLUMN {col_name} {col_def}")
        conn.commit()
    finally:
        conn.close()


@contextmanager
def connect(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open a connection with the W4 schema guaranteed in place."""
    ensure_schema(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_answer(
    conn: sqlite3.Connection,
    *,
    question: str,
    content: str,
    retries: int,
    cost_usd: float,
    model: str,
    confidence: float,
    sources: list[str],
    schema_version: str = "v1",
) -> int:
    """Insert one row and return its rowid."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(answers)").fetchall()}
    if "answer" in columns:
        cur = conn.execute(
            """
            INSERT INTO answers (
                question, answer, content, retries, cost_usd, model,
                confidence, sources_json, schema_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                content,
                content,
                retries,
                cost_usd,
                model,
                confidence,
                json.dumps(sources),
                schema_version,
            ),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO answers (
                question, content, retries, cost_usd, model,
                confidence, sources_json, schema_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                content,
                retries,
                cost_usd,
                model,
                confidence,
                json.dumps(sources),
                schema_version,
            ),
        )
    return cur.lastrowid


def write_eval_run(
    conn: sqlite3.Connection,
    *,
    golden_id: str,
    question: str,
    candidate_answer: str,
    ideal_answer: str,
    judge_model: str,
    scores: dict,
    label: str,
) -> int:
    """Insert one evaluated answer and return its row id."""
    cur = conn.execute(
        """
        INSERT INTO eval_runs (
            golden_id, question, candidate_answer, ideal_answer,
            candidate_model, judge_model, accuracy, groundedness, format,
            reasoning, eval_run_label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            golden_id,
            question,
            candidate_answer,
            ideal_answer,
            "api",
            judge_model,
            scores["accuracy"],
            scores["groundedness"],
            scores["format"],
            scores["reasoning"],
            label,
        ),
    )
    return cur.lastrowid


def query_results(conn: sqlite3.Connection, model: str | None = None) -> list[dict]:
    """Read back rows, optionally filtered by model. Useful in Step 3."""
    if model is None:
        cur = conn.execute("SELECT * FROM answers ORDER BY id")
    else:
        cur = conn.execute(
            "SELECT * FROM answers WHERE model = ? ORDER BY id", (model,)
        )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]