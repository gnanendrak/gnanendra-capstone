# wk6-snapshot.md — Naive RAG baseline

**Date:** YYYY-MM-DD
**Corpus:** N documents, M chunks
**Golden set:** 20 questions

## Headline numbers

| Metric | W6 baseline | Target for W7 |
|---|---|---|
| Cost per query (USD) | $0.00007172 | ↓ (embed cache) |
| Latency p50 (ms) | XXX | ↓ (vector DB, no full scan) |
| Retrieval hit rate | 0 | ↑ (structure-aware chunking) |
| Grounded response rate | 60% | ↑ (better retrieval) |
| Hallucination rate | XX% | ↓ (better retrieval) |

## Method
- Ran all 20 golden-set questions through `ask_rag` with k=3
- Judged with W5 `judge.py` (grounded rubric)
- Cost = embedding tokens (~$0.02/1M) + gpt-4o-mini tokens

## Top 3 limits observed
1. [Chunking cuts mid-sentence — example: chunk XX]
2. [Retrieval picks off-topic chunks for questions like: XX]
3. [Prompt doesn't always cite sources — example: question YY answered without brackets]

## What W7-W11 will improve
- W7: proper chunking + Qdrant vector DB
- W8: cost tracking via embedding cache
- W9: hybrid search (BM25 + dense) + rerank
- W10: caching + KB lifecycle