"""Week 5 - run the critic/creator loop on a weak answer and save the trace.

Takes the first golden question, gets the app's current answer as the draft,
then loops critic <-> creator until it satisfies the rubric. Writes the
round-by-round trace to docs/critic-creator-trace.md.

Prereqs: API running + OPENAI_API_KEY (or USE_FAKE=1 for an offline dry run).
Usage:   python scripts/run_critic_creator.py
"""

from __future__ import annotations
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import argparse
import httpx
from pathlib import Path

from src.eval.golden import load_golden

API_URL = "http://localhost:8000/ask_batched"
DEFAULT_GOLDEN_SET = "data/hr_golden_set_20.jsonl"
DEFAULT_REPORT = "docs/critic-creator-trace.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a critic/creator loop")
    parser.add_argument("--golden-set", default=DEFAULT_GOLDEN_SET)
    parser.add_argument("--golden-id", required=True)
    parser.add_argument("--creator-model", default="gpt-4o-mini")
    parser.add_argument("--judge-model", default="gpt-4o")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=3.5)
    parser.add_argument("--output", default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def get_candidate(question: str) -> str:
    r = httpx.post(API_URL, json={"question": question}, timeout=60.0)
    r.raise_for_status()
    return r.json()["content"]


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    golden = load_golden(args.golden_set)
    g = next((entry for entry in golden if entry.id == args.golden_id), None)
    if g is None:
        raise SystemExit(f"Golden ID {args.golden_id!r} not found in {args.golden_set}")

    draft = get_candidate(g.question)
    from src.eval.critic_creator import critic_creator

    result = critic_creator(
        g.question,
        draft,
        g.must_mention,
        creator_model=args.creator_model,
        judge_model=args.judge_model,
        max_rounds=args.max_rounds,
        threshold=args.threshold,
    )

    lines = [
        f"# Critic-Creator trace - {g.id}",
        "",
        f"**Question:** {g.question}",
        "",
        f"**Initial draft:** {draft}",
        "",
    ]
    for step in result["trace"]:
        lines += [
            f"## Round {step['round']}",
            f"- answer: {step['answer']}",
            f"- issues: {step['issues'] or 'none'}",
            "",
        ]
    lines += [f"**Final ({result['rounds']} rounds):** {result['final']}", ""]
    report_path = Path(args.output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}  ({result['rounds']} rounds)")
    print("FINAL:", result["final"])


if __name__ == "__main__":
    main()