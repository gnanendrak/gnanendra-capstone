
**Date:** 2026-10-17
**Vector store:** Qdrant Cloud
**Collection:** `capstone_chunks_v2` (800 points, 1536 dimensions, cosine)
**Chunking strategy:** recursive, max chunk size 400 characters
**PII scrubbing:** regex + Presidio hybrid

## Headline numbers

| Metric | W7 (`capstone_chunks`, eval-run-008) | W8 (`capstone_chunks_v2`, eval-run-w8-chunks-20261017-final) | W8 minus W7 |
|---|---:|---:|---:|
| Average candidate cost/query | $0.00007675 | $0.00004973 | -$0.00002702 (-35.2%) |
| Candidate latency p50 | 2777.5 ms | 2652.1 ms | -125.4 ms (-4.5%) |
| Any expected-source hit@3 | 20/20 (100%) | 20/20 (100%) | 0 pp |
| Complete expected-source hit@3 | 17/20 (85%) | 17/20 (85%) | 0 pp |
| Mean expected-source coverage@3 | 91.2% | 91.2% | 0 pp |
| Mean accuracy | 2.90 / 4 | 2.30 / 4 | -0.60 |
| Mean groundedness | 2.90 / 4 | 2.45 / 4 | -0.45 |
| Mean format | 3.20 / 4 | 3.00 / 4 | -0.20 |
| PII detector flags | Not measured in W7 | 74 across 59 of 800 chunks | W8 detector/audit capability added |

PII counts are detector flags for review, not independently verified PII items.
See `docs/wk8-pii-audit.md` for the sample and its limitations.

## Operational deltas

| Property | W7 | W8 |
|---|---|---|
| Metadata fields per chunk | 3 in W7 payload | 11 in W8 payload |
| Filtering | No W7 metadata filters | Metadata is available to support filters; filtering is not yet applied in the current retrieval query |
| PII handling | No W7 PII audit recorded | Regex + Presidio detector/scrub pass at ingestion; 74 flags raised for review |

## Method
- Same 20 questions from `data/golden_set.jsonl`; W7 and W8 use `gpt-4o-mini` answers and `gpt-4o` judging.
- W7 baseline: `eval-run-008-small-embedding-20261014`; W8: `eval-run-w8-chunks-20261017-final`.
- Retrieval hit uses expected document IDs in the golden set. Complete-source hit requires every expected document among top 3; coverage gives partial credit. Chunk IDs are normalized to parent document IDs.
- Cost is candidate API cost only; judge cost is excluded. W8 values cover 20 candidate calls. Median latency is end-to-end API request time.

## Interpretation

On this 20-question run, source retrieval metrics did not change: any-source
hit@3 remained 100%, complete-source hit@3 remained 85%, and mean expected-source
coverage remained 91.2%. W8 judge scores decreased, with accuracy down 0.60,
groundedness down 0.45, and format down 0.20 points. This shows that retrieving
an expected source is not sufficient to ensure the answer uses it correctly.

Candidate cost/query was 35.2% lower and median latency 4.5% lower in W8. The
reports do not isolate whether those differences came from chunking, payload
size, prompt context, or run variability; metadata is stored but the current
retrieval function does not apply metadata filters. Do not attribute the score
or latency changes to a single W8 feature without a controlled ablation.