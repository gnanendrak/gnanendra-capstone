# W8 PII Audit — capstone_chunks_v2

**Date:** 2026-11-05
**Corpus:** `data/corpus/` (24 documents)
**Collection:** `capstone_chunks_v2`
**Total chunks ingested:** 1878
**PII detector flags:** 187 (9.96%)

## Sample audit — 10 returned chunks

Fetched via:
```python3 -c 
"from src.rag.qdrant_store import _get_client
client = _get_client()
sample = client.scroll(collection_name="capstone_chunks_v2", limit=10, with_payload=True)[0]"
```

The supplied scroll returns the first page of points, not a random sample. These
ten records are all from `01_employee_handbook.md`, so they are not representative
of all source documents.

| Chunk ID | Source | Stored PII flag count | Payload metadata present |
|---|---|---:|---|
| `01_employee_handbook#0` | `01_employee_handbook.md` | 2 | yes |
| `01_employee_handbook#1` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#2` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#3` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#4` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#5` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#6` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#7` | `01_employee_handbook.md` | 1 | yes |
| `01_employee_handbook#8` | `01_employee_handbook.md` | 0 | yes |
| `01_employee_handbook#9` | `01_employee_handbook.md` | 0 | yes |

Sample total: 3 flags across 2 of 10 chunks. The stored count reflects the
ingestion detector's matches; flags are indicators for review, not confirmation
that the content is personal data. The full collection contains 187 detector
flags across out of 1878 chunks.