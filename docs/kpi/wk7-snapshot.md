# wk7-snapshot.md — Qdrant migration baseline

**Date:** YYYY-MM-DD
**Vector store:** Qdrant Cloud
**Collection:** capstone_chunks (N points, 1536 dim, cosine)
**Embedding model:** text-embedding-3-small

## Headline numbers

| Metric | W6 (JSON) | W7 (Qdrant) | Delta |
|---|---|---|---|
| Cost per query | $0.000XXX | $0.000XXX | ≈ 0 (no new embeds) |
| Latency p50 (ms) | XXX | XXX | may decrease slightly |
| Retrieval hit rate | XX% | XX% | should NOT change |
| Grounded response rate | XX% | XX% | should NOT change |

## Operational deltas (the real W7 win)

| Property | W6 | W7 |
|---|---|---|
| Persistence | file-based JSON | Qdrant-managed |
| Restart cost | O(N) load into memory | O(1) — Qdrant already loaded |
| Filtering | none | ready for W8 metadata |
| Scaling ceiling | ~10K chunks (RAM) | millions (HNSW) |

## Method
- Same 20 golden-set questions from W5
- W6 numbers from wk6-snapshot.md
- W7 numbers from a fresh run against Qdrant collection

## Embedding-model comparison (from Lab Step 2)
- text-embedding-3-small: XX/20 correct retrieval, $X.XX total
- text-embedding-3-large: XX/20 correct retrieval, $X.XX total
- **Choice for ADR:** text-embedding-3-small (default) OR text-embedding-3-large
- **Reason:** [why you picked what you picked]