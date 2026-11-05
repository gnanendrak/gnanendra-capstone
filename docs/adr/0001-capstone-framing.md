# ADR-0001: Capstone Framing — HR Policy Knowledge Assistence

- **Status:** Draft v1
- **Date:** 2026-08-25
- **Author:** Kanala Gnanendra Reddy

## Context

what problem is this capstone trying to solve, for whom, and why now?(2–3 sentences)

## Decision — Solution Framing Canvas

| Box | Your answer |
|-----|-------------|
| **Inputs** | what the user / caller sends — text, file uploads, parameters |
| **Outputs** | what the system produces — a text answer, a citation list, a structured result |
| **Tools** | what external services it uses — OpenAI, your retriever, a database, … |
| **Memory** | what the system remembers between calls — nothing, last N turns, durable history |
| **Autonomy level** | on the spectrum from chatbot to agentic system, where this sits and why |
| **Decision boundaries** | what it's allowed to decide on its own, vs. what needs a human |

## Consequences

- **Positive:**
  - How this benefits to HR (point 1) 
  - How this benefits to HR (point 2) 
  - How this benefits to HR (point 3) 

- **Negative / Risks:**
  - What are the risks (point 1) 
  - What are the risks (point 2) 
  - What are the risks (point 3) 

- **Things we'll re-visit:**
  - specific things we'll come back to in later ADRs (1)
  - specific things we'll come back to in later ADRs (2)
  - specific things we'll come back to in later ADRs (3)
  
## Consequences

### Positive

- How this benefits to HR (point 1) 
- How this benefits to HR (point 2) 
- How this benefits to HR (point 3) 

### Negative / risks

- What are this risks (point 1) 
- What are this risks (point 2) 
- What are this risks (point 3) 

### Things we'll re-visit

- specific things we'll come back to in later ADRs (1)
- specific things we'll come back to in later ADRs (2)
- specific things we'll come back to in later ADRs (3)


## W6 — Naive RAG live

**Decision:** Naive RAG is now the default answer path. `/ask_batched` retrieves
top-3 chunks from `data/corpus/` before generating.

**Baseline KPIs** (see docs/kpi/wk6-snapshot.md):
- Cost/query: $0.000XXX
- Latency p50: XXX ms
- Grounded response rate: XX%

**Top 3 known limits** (to be addressed W7-W11):
1. Chunking cuts mid-sentence — W7 fixes with structure-aware chunker
2. Retrieval is pure dense — W9 adds BM25 hybrid
3. No metadata filtering — W7 introduces via Qdrant payload

**Status:** In production for the demo API. Not yet suitable for real users;
retrieval quality needs W7-W9 improvements first.


## W7 — Qdrant-backed vector store
## W7 — Qdrant-backed vector store

**Decision:** Capstone now uses Qdrant Cloud (free tier) as the vector store.
`naive_rag.py` retained as reference.

**Vector stack:**
- Embedding model: text-embedding-3-small (1536 dims, $0.02 per 1M tokens)
- Vector store: Qdrant Cloud
- Distance metric: cosine (programme default; see W7 Track A Day 2 for why)
- Index: HNSW with defaults (m=16, ef_construct=100)

**Rejected alternatives:**
- text-embedding-3-large — 6.5× cost, insufficient quality gain on our corpus (see Lab Step 2)
- FAISS — no service layer; we need persistence + REST
- Chroma — smaller ecosystem, less battle-tested
- pgvector — no existing Postgres; not worth adding

**Operational KPIs** (see docs/kpi/wk7-snapshot.md):
- Persistence: Qdrant-managed (was: JSON file on disk)
- Restart cost: O(1) — no re-load of vectors into memory
- Ready for W8 metadata filtering