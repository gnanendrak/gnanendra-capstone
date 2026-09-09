"""api/main.py — STARTER for Week 3 Lab Step 1.

You will complete this file across sub-steps 1b → 1f. Each TODO matches a
sub-step in the lab guide.

The completed reference is at <cohort-repo>/week3/reference/api_main_reference.py.

Architecture note: this file holds the *public* W3 API contract — Question
with field `question`, Answer with fields `content/cost_usd/retries`. These
are locked in ADR 0002. Internally we delegate to the W2 pipeline's
`ask_llm`, whose Question has field `text` and whose Answer has field `text`.
The translation happens inside each endpoint.
"""
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# W2 pipeline — the underlying engine
from src.pipeline.pipeline import ask_llm as _pipeline_ask_llm
from src.pipeline.pipeline import Question as _PipelineQuestion


# ─────────────────────────────────────────────────────────────────────────────
# Public W3 API models — locked in ADR 0002
# ─────────────────────────────────────────────────────────────────────────────
class Question(BaseModel):
    """Public request shape. Field name `question`, not `text`."""
    question: str


class Answer(BaseModel):
    """Public response shape. Field name `content`, not `text`."""
    content: str
    cost_usd: float
    retries: int


# ─────────────────────────────────────────────────────────────────────────────
# 1b — Replace the placeholder below with a real FastAPI app instance.
# ─────────────────────────────────────────────────────────────────────────────
app=FastAPI(
    title="Capstone API",
    description="Wraps the W2 async pipeline. Contract locked in ADR 0002 (W3); internals upgraded W4+.",
    version="1.0.0"
)


# ─────────────────────────────────────────────────────────────────────────────
# /ask_batched — non-streaming reference endpoint
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/ask_batched", response_model=Answer)
async def ask_batched(q: Question) -> Answer:
    """Non-streaming. Returns the full Answer in a single JSON body."""
    pipeline_q=_PipelineQuestion(text=q.question)
    pipeline_ans=await _pipeline_ask_llm(pipeline_q)
    return Answer(
        content=pipeline_ans.text,
        cost_usd=pipeline_ans.cost_usd,
        retries=pipeline_ans.retries
    )


# ─────────────────────────────────────────────────────────────────────────────
# /health — liveness probe
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# /ask — streaming endpoint (the contracted one)
# ─────────────────────────────────────────────────────────────────────────────
async def stream_answer(question_text: str):
    """Async generator yielding the answer word-by-word.

    W3 streams from FastAPI to the client; the pipeline call itself is still
    non-streaming. In W4 the LLM call becomes a real stream end-to-end — this
    generator's shape doesn't change, only what fills it.
    """

    pipeline_q=_PipelineQuestion(text=question_text)
    pipeline_ans=await _pipeline_ask_llm(pipeline_q)
    for word in pipeline_ans.text.split(" "):
        yield word + " "
        asyncio.sleep(0.05)


@app.post("/ask")
async def ask(q: Question):
    """Streaming /ask — the contracted endpoint."""
    return StreamingResponse(
        stream_answer(q.question),
        media_type="text/plain"
    )
