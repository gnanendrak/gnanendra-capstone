"""Week 5 - pairwise sanity check with position-flip.

For each golden question, compare the app's answer against the golden IDEAL
answer using pairwise_consistent (which always flips position). Reports how
often the app answer wins / ties / loses vs the ideal. Extend this to compare
your own prompt v1 vs v2 answers.

Prereqs: API running + OPENAI_API_KEY (or USE_FAKE=1 for an offline dry run).
Usage:   python scripts/run_pairwise.py
"""

from __future__ import annotations
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import httpx
import argparse
from pathlib import Path

from src.eval.golden import load_golden
from src.eval.pairwise import pairwise_consistent

DEFAULT_API_URL = "http://localhost:8000/ask_batched"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the app against a golden set"
    )
    parser.add_argument("--prompt-v1", default="data/prompt-v1.txt")
    parser.add_argument("--prompt-v2", default="data/prompt-v2.txt")
    parser.add_argument("--golden-set", default="data/golden_set.jsonl")
    # parser.add_argument("--db", default="data/answers.db")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--judge-model", default="gpt-4o")
    parser.add_argument("--output", default="data/pairwise-001-results.json")
    return parser.parse_args(argv)


def get_candidate(question: str) -> str:
    r = httpx.post(DEFAULT_API_URL, json={"question": question}, timeout=60.0)
    r.raise_for_status()
    return r.json()["content"]


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    golden = load_golden(args.golden_set)
    report_path = Path(args.output)
    tally = {"APP": 0, "IDEAL": 0, "TIE (order-dependent)": 0}
    rows = []
    for g in golden:
        app_answer = get_candidate(g.question)
        winner = pairwise_consistent(
            g.question, ("APP", app_answer), ("IDEAL", g.ideal_answer)
        )
        tally[winner] = tally.get(winner, 0) + 1
        rows.append((g.id, winner))
        print(f"{g.id}: winner = {winner}")
    print("\nTotals:", tally)

    lines = [
        f"# Pairwise comparison summary ({len(rows)} golden questions)",
        "",
        f"- Golden set: `{args.golden_set}`",
        f"- Prompt v1: `{args.prompt_v1}`",
        f"- Prompt v2: `{args.prompt_v2}`",
        "",
        "## Totals",
        "",
        "| Outcome | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {outcome} | {count} |" for outcome, count in tally.items())
    lines.extend(["", "## Per-question results", "", "| ID | Winner |", "|---|---|"])
    lines.extend(f"| {question_id} | {winner} |" for question_id, winner in rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote summary to {report_path}")


if __name__ == "__main__":
    main()