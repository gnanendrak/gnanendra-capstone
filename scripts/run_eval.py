"""Week 5 - run the golden set through the app and judge every answer.

Flow:  load golden set -> POST each question to /ask_batched -> judge the answer
against the ideal -> persist to eval_runs -> write docs/eval-run-001.md.

Prereqs:
  * the API running:   uvicorn api.main:app --port 8000
  * OPENAI_API_KEY set (real judge = gpt-4o), OR run offline: USE_FAKE=1 python scripts/run_eval.py

Usage:  python scripts/run_eval.py
"""

from __future__ import annotations
import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from src.eval.golden import load_golden
from src.eval.judge import judge
from src.pipeline import store

DEFAULT_API_URL = "http://localhost:8000"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the app against a golden set"
    )
    parser.add_argument("--golden-set", default="data/golden_set.jsonl")
    parser.add_argument("--db", default="data/answers.db")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--judge-model", default="gpt-4o")
    parser.add_argument("--label", default="eval-run-002")
    return parser.parse_args(argv)


def get_candidate(question: str, api_url: str) -> tuple[str, list[str]]:
    """Ask the running app for an answer."""
    endpoint = api_url.rstrip("/")
    if not endpoint.endswith("/ask_batched"):
        endpoint += "/ask_batched"
    r = httpx.post(endpoint, json={"question": question}, timeout=60.0)
    r.raise_for_status()
    data = r.json()
    return data["content"], data.get("sources", [])


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    golden = load_golden(args.golden_set)
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    run_id = int(time.time())
    report_path = Path("docs") / f"{args.label}.md"

    rows, accs, grds, fmts = [], [], [], []
    with store.connect(db_path) as con:
        for g in golden:
            candidate, _sources = get_candidate(g.question, args.api_url)
            s = judge(
                g.question,
                g.ideal_answer,
                candidate,
                g.must_mention,
                model=args.judge_model,
            )
            store.write_eval_run(
                con,
                golden_id=g.id,
                question=g.question,
                candidate_answer=candidate,
                ideal_answer=g.ideal_answer,
                judge_model=args.judge_model,
                scores=s,
                label=args.label,
            )
            rows.append((g.id, candidate, s))
            accs.append(s["accuracy"])
            grds.append(s["groundedness"])
            fmts.append(s["format"])
            print(
                f"{g.id}: acc={s['accuracy']} grnd={s['groundedness']} fmt={s['format']}  "
                f"| {candidate[:60]}"
            )

    n = len(rows)
    avg = lambda xs: round(statistics.mean(xs), 2) if xs else 0.0
    lines = [
        f"# {args.label} ({n} golden questions)",
        "",
        f"- run_id: `{run_id}`",
        f"- avg accuracy:     **{avg(accs)}** / 4",
        f"- avg groundedness: **{avg(grds)}** / 4",
        f"- avg format:       **{avg(fmts)}** / 4",
        "",
        "| id | acc | grnd | fmt | candidate |",
        "|----|-----|------|-----|-----------|",
    ]
    for gid, cand, s in rows:
        c = cand.replace("|", "/")[:70]
        lines.append(
            f"| {gid} | {s['accuracy']} | {s['groundedness']} | {s['format']} | {c} |"
        )
    with report_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {report_path}  (avg accuracy {avg(accs)}/4 over {n} questions)")


if __name__ == "__main__":
    main()