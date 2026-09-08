"""Async batch pipeline — COMPLETED REFERENCE for Week 2.

Demonstrates the full Week 2 architecture:
  - Typed Settings (Pydantic v2) with field constraints
  - JSON logging to logs/pipeline.log via logging_config
  - CSV-driven input via load_questions
  - Async batched parallel calls (chunks of `batch_size`) with retry + backoff
  - RunSummary aggregation per execution
  - results.json output (summary + answers)
  - SQLite persistence via store (deferred import)
  - Switchable fake/real LLM via Settings.use_fake

Run with:
    python -m src.pipeline.pipeline
"""
from __future__ import annotations
import asyncio
import csv
import json
import time
from tqdm import tqdm
from pathlib import Path

from .logging_config import get_logger
from .settings import Settings, RunSummary
# ─────────────────────────────────────────────────────────────────────────────
# Logger — shared across the package
# ─────────────────────────────────────────────────────────────────────────────
log=get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# LLM client setup — branches on Settings.use_fake at module-load time
# ─────────────────────────────────────────────────────────────────────────────
_settings_for_import=Settings()

if _settings_for_import.use_fake:
    from .fake_llm import fake_ask_llm, Question, Answer, FakeLLMError
else:
    from dotenv import load_dotenv
    from openai import AsyncOpenAI
    from pydantic import BaseModel, Field, ValidationError

    load_dotenv()
    _client=AsyncOpenAI()

    class Question(BaseModel):
        text: str

    class Answer(BaseModel):
        question: str
        text:     str
        cost_usd: float
        retries:  int=0


# ─────────────────────────────────────────────────────────────────────────────
# CSV loader
# ─────────────────────────────────────────────────────────────────────────────
def load_questions(
        path: str | Path="data/questions.csv"
        ) ->list[Question]:
    """Read questions from a CSV with a `text` column."""
    with open(path, newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    return [Question(text=row["text"]) for row in rows if row.get("text")]


# ─────────────────────────────────────────────────────────────────────────────
# 2b — single LLM call
# ─────────────────────────────────────────────────────────────────────────────
async def ask_llm(q: Question, fail_rate: float=0.0) -> Answer:
    """One LLM call. Fake for now; real client wired in via Settings.use_fake later."""

    if _settings_for_import.use_fake:
        ans=await fake_ask_llm(q, fail_rate=fail_rate)
    else:
       resp=await _client.chat.completions.create(
            model=_settings_for_import.model,
            messages=[
                {"role": "user", "content": q.text}
            ]
        )
       ans=Answer(
            question=q.text,
            text=resp.choices[0].message.content,
            cost_usd=0.0001
       )
    log.info(f"asked: {q.text[:40]}")
    return ans


# ─────────────────────────────────────────────────────────────────────────────
# 2c — retry wrapper
# ─────────────────────────────────────────────────────────────────────────────
async def ask_llm_with_retry(
    q: Question, 
    tries: int=3, 
    fail_rate: float=0.0
) -> Answer:
    """Retry up to `tries` times. Wait 1 s, 2 s, 4 s between attempts."""
    
    for attempt in range(tries):
        try:
            ans=await ask_llm(q, fail_rate=fail_rate)
            ans.retries=attempt
            log.info(f"asked: {q.text[:40]}")
            return ans
        except Exception as exc:
            if attempt == tries-1:
                raise
            log.warning(f"retry {attempt + 1} for: {q.text[:40]} ({exc})")
            await asyncio.sleep(2**attempt)

    raise RuntimeError("unreachable")


# ─────────────────────────────────────────────────────────────────────────────
# 2d — batch runner
# ─────────────────────────────────────────────────────────────────────────────
async def run_batch(
        questions: list[Question], fail_rate: float=0.0
        ) -> list[Answer]:
    """Fire every question in parallel via asyncio.gather (with retries)."""

    task=[ask_llm_with_retry(q, fail_rate=fail_rate) for q in questions]
    return await asyncio.gather(*task)

async def run_in_batches(
        questions: list[Question], 
        batch_size: 5,
        fail_rate: float=0.0
        ) -> list[Answer]:
    """Fire questions in chunks of `batch_size`, with a 100 ms pause between batches."""

    progress = tqdm(
        total=len(questions),
        desc="Processing questions",
        unit="question",
    )

    out: list[Answer]=[]
    for i in range(0, len(questions), batch_size):
        chunk=questions[i:i+batch_size]
        log.info(f"batch {i // batch_size + 1}: {len(chunk)} questions")
        batch_answers=await asyncio.gather(
            *(ask_llm_with_retry(q, fail_rate=fail_rate) for q in chunk)
            )
        out.extend(batch_answers)
        await asyncio.sleep(0.1)
        progress.update(len(chunk))
    progress.close()

    return out


# ─────────────────────────────────────────────────────────────────────────────
# Run summariser
# ─────────────────────────────────────────────────────────────────────────────
def summarise_run(
        answers:list[Answer],
        *,
        started_at: float,
        elapsed: float,
        fail_rate: float,
        use_fake: bool
) -> RunSummary:
    """Roll a list of Answers + wall-clock data into a RunSummary."""

    return RunSummary(
        started_at=started_at,
        elapsed_seconds=elapsed,
        n_questions=len(answers),
        n_succeeded= len(answers),
        n_retries_total=sum(a.retries for a in answers),
        total_cost_usd=sum(a.cost_usd for a in answers),
        fail_rate=fail_rate,
        use_fake=use_fake
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint — replaced in Step 3a (Settings) and again in Step 3c (CSV + batched)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    settings=Settings()
    log.info(f"config:{settings.model_dump(mode='json')}")
    questions=load_questions(settings.questions_csv)
    log.info(f"loaded {len(questions)} questions")

    started=time.time()
    answers=asyncio.run(
        run_in_batches(
            questions,
            batch_size=settings.batch_size,
            fail_rate=settings.fail_rate))
    elapsed=time.time()-started
    #log.info(f"done: {len(answers)} answers in {elapsed}s")

    summary=summarise_run(
        answers,
        started_at=started,
        elapsed=elapsed,
        fail_rate=settings.fail_rate,
        use_fake=settings.use_fake
    )
    log.info(f"summary: {summary.model_dump_json()}")

    # Write the structured artefact
    settings.results_json.write_text(
        json.dumps({
            "summary":summary.model_dump(),
            "answers":[a.model_dump() for a in answers],
        }, indent=2)
    )
    print(f"wrote {len(answers)} answers to {settings.results_json} in {elapsed:.2f}s")

    # SQLite persistence
    # Deferred import: store.py imports Answer from this module; top-level import
    # would cause a circular import.
    from .store import connect, write_run, write_answers
    with connect(settings.results_db) as con:
        run_id=write_run(con,summary)
        n=write_answers(con, run_id, answers)
    log.info(f"persisted run {run_id} with {n} answersto {settings.results_db}")

    totalCost=sum(a.cost_usd for a in answers)
    log.info(f"total-cost: {totalCost}")

    