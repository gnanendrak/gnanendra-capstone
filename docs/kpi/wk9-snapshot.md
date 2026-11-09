# wk9-snapshot.md — Hybrid retrieval + reranking baseline

**Date:** YYYY-MM-DD
**Retrieval stack:** BM25 (rank-bm25) + Dense (Qdrant cosine, text-embedding-3-small) via RRF (k=60) → Cross-encoder rerank (ms-marco-MiniLM-L-6-v2, top-3)

## Headline numbers

| Metric | W8 (dense-only) | W9 (hybrid+rerank) | Delta |
|---|---|---|---|
| Precision@3 | X.XX | Y.YY | +Z.ZZ |
| Precision@5 | X.XX | Y.YY | +Z.ZZ |
| Grounded response rate | X.XX | Y.YY | +Z.ZZ |
| Cost per query | $X.XX | $Y.YY | ≈ +$0.0001 (no new embed for rerank) |
| Latency p50 (ms) | XXX | YYY | +Z ms (mostly rerank CPU) |

## Method
- Same 20 golden-set questions from W5
- W8 numbers from wk8-snapshot.md
- W9 numbers from scripts/measure_wk9_precision.py (Cell 2 output)
- Grounded response rate: re-ran W4 judge on new retrievals

## What changed structurally
- W8 used pure dense retrieval; W9 adds BM25 + cross-encoder reranker
- Latency increased by ~150-200ms per query (mostly cross-encoder CPU)
- Cost per query essentially unchanged (rerank is local, not API)
- Precision@3 lifted from Y.YY to Z.ZZ — see docs/wk9-precision-delta.md for per-question

## Interpretation
[why did numbers move? which failure modes did hybrid fix? which did rerank fix?]