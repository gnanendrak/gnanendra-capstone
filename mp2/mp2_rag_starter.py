"""MP2 · Mini-RAG — Starter Template
====================================

You'll build a complete RAG pipeline over the Sherlock Holmes corpus in this
file. Fill in every TODO. The reference solution is ~250 lines, but yours can
be shorter or longer — what matters is that it works end-to-end.

Pipeline you're building:
    corpus/*.txt  →  chunks  →  embeddings  →  Qdrant
                                                  ↓
                              question  →  retrieve  →  answer + citations

Run sequence (once you've filled in the TODOs):
    pip install -r requirements.txt
    source .env                 # exports your OpenAI + Qdrant credentials
    python mp2_rag.py ingest    # builds the collection (run once)
    python mp2_rag.py ask       # interactive Q&A loop
    python mp2_rag.py validate  # runs against data/predefined_questions.jsonl

Tip: get the CORE pipeline working FIRST (Steps 1-7 below), THEN come back to
polish and add your 3 questions. Don't try to perfect each step before moving
on — you'll learn more from a rough end-to-end loop than a polished half.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# ─── Configuration ──────────────────────────────────────────────────────

load_dotenv()

print("Loading environment variables…")
CORPUS_DIR        = Path(__file__).parent / "corpus"
DATA_DIR          = Path(__file__).parent / "data"
COLLECTION_NAME   = "mp2_sherlock"
EMBEDDING_MODEL   = "text-embedding-3-small"
EMBEDDING_DIM     = 1536
CHAT_MODEL        = "gpt-4o-mini"
TARGET_CHUNK_SIZE = 500   # characters
CHUNK_OVERLAP     = 80    # characters

openai = OpenAI()
qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ.get("QDRANT_API_KEY"),
    timeout=60,
)


# ─── Step 1: Load the corpus ────────────────────────────────────────────

def load_corpus(corpus_dir: str) -> list[dict]:
    """Read every .txt file in the corpus directory.

    Returns a list of dicts, each with: source (filename), title (first line),
    and text (full content).
    """

    docs = []
    corpus_path = Path(corpus_dir)

    for file_path in corpus_path.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        title = next(
            (line.strip() for line in text.splitlines() if line.strip()),
            ""
        )

        docs.append({
            "source": file_path.name,
            "title": title,
            "text": text
        })

    print(f"Loaded {len(docs)} documents from {corpus_dir}")
    return docs


# ─── Step 2: Chunk each document ────────────────────────────────────────

def chunk_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Split a document into smaller chunks.

    Each chunk should be a dict with: source, title, section, text.

    Use paragraph and sentence boundaries as practical semantic units, packing
    them up to TARGET_CHUNK_SIZE characters. Short lines without terminal
    punctuation are treated as section headings.
    """

    text = str(doc.get("text", "")).strip()
    title = str(doc.get("title", ""))
    source = str(doc.get("source", ""))
    if not text:
        return []

    chunks: list[dict[str, Any]] = []
    section = title
    current_units: list[tuple[int, str]] = []

    def render(units: list[tuple[int, str]]) -> str:
        parts: list[str] = []
        previous_paragraph: int | None = None
        for paragraph_index, unit in units:
            separator = (
                "\n\n"
                if previous_paragraph is not None
                and paragraph_index != previous_paragraph
                else " "
            )
            parts.append(f"{separator}{unit}" if parts else unit)
            previous_paragraph = paragraph_index
        return "".join(parts)

    def flush() -> None:
        nonlocal current_units
        if current_units:
            chunks.append({
                "source": source,
                "title": title,
                "section": section,
                "text": render(current_units),
            })
            current_units = []

    def split_sentences(paragraph: str) -> list[str]:
        sentences: list[str] = []
        start = 0
        index = 0
        in_quote = False
        abbreviations = {"dr", "mr", "mrs", "ms", "prof", "st", "jr", "sr"}

        while index < len(paragraph):
            character = paragraph[index]
            if character in {'"', "“"}:
                in_quote = not in_quote
            elif character == "”":
                in_quote = False

            if character not in ".!?":
                index += 1
                continue

            if character == ".":
                abbreviation = re.search(
                    r"([A-Za-z]+)\.$",
                    paragraph[start:index + 1],
                )
                if abbreviation and abbreviation.group(1).lower() in abbreviations:
                    index += 1
                    continue

            end = index + 1
            closes_quote = False
            while end < len(paragraph) and paragraph[end] in "\"”')]}":
                if paragraph[end] in "\"”":
                    closes_quote = True
                end += 1

            if in_quote and not closes_quote:
                index += 1
                continue
            if end < len(paragraph) and not paragraph[end].isspace():
                index += 1
                continue

            sentence = paragraph[start:end].strip()
            if sentence:
                sentences.append(sentence)
            start = end
            while start < len(paragraph) and paragraph[start].isspace():
                start += 1
            index = start
            in_quote = False

        remainder = paragraph[start:].strip()
        if remainder:
            sentences.append(remainder)
        return sentences

    for paragraph_index, paragraph in enumerate(re.split(r"\n\s*\n", text)):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph == title and not chunks and not current_units:
            continue

        is_heading = (
            len(paragraph) <= 80
            and not re.search(r"[.!?][\"')\]]?$", paragraph)
        )
        if is_heading:
            flush()
            section = paragraph
            continue

        for sentence in split_sentences(paragraph):
            units = [(paragraph_index, sentence)]
            if len(sentence) > TARGET_CHUNK_SIZE:
                flush()
                words = sentence.split()
                fragment: list[str] = []
                fragment_length = 0
                for word in words:
                    added_length = len(word) + (1 if fragment else 0)
                    if fragment and fragment_length + added_length > TARGET_CHUNK_SIZE:
                        chunks.append({
                            "source": source,
                            "title": title,
                            "section": section,
                            "text": " ".join(fragment),
                        })
                        fragment = []
                        fragment_length = 0
                        added_length = len(word)
                    fragment.append(word)
                    fragment_length += added_length
                if fragment:
                    chunks.append({
                        "source": source,
                        "title": title,
                        "section": section,
                        "text": " ".join(fragment),
                    })
                continue

            if (
                current_units
                and len(render(current_units + units)) > TARGET_CHUNK_SIZE
            ):
                previous_units = current_units
                flush()
                overlap = [previous_units[-1]]
                if (
                    len(overlap[0][1]) <= CHUNK_OVERLAP
                    and len(render(overlap + units)) <= TARGET_CHUNK_SIZE
                ):
                    current_units = overlap
            current_units.extend(units)

    flush()
    return chunks


# ─── Step 3: Embed text ─────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of texts using OpenAI's embedding model.

    Returns a list of 1536-dim float vectors (same order as inputs).
    """
    
    BATCH_SIZE = 200
    all_embeddings: list[list[float]] = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]

        response = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )

        # Preserve the order of texts within each batch.
        batch_embeddings = sorted(
            response.data,
            key=lambda item: item.index,
        )

        all_embeddings.extend(
            item.embedding for item in batch_embeddings
        )

    return all_embeddings


# ─── Step 4: Set up the Qdrant collection ───────────────────────────────

def setup_collection() -> None:
    """Create (or recreate) the Qdrant collection."""

    if qdrant.collection_exists(COLLECTION_NAME):
        qdrant.delete_collection(COLLECTION_NAME)

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )


# ─── Step 5: Ingest chunks into Qdrant ──────────────────────────────────

def ingest_chunks(chunks: list[dict[str, Any]]) -> None:
    """Embed every chunk and upsert into Qdrant."""

    if not chunks:
        print("No chunks to ingest.")
        return
    
    # 1. Validate chunks
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise TypeError(f"Chunk at index {index} must be a dictionary.")

        if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
            raise ValueError(f"Chunk at index {index} has missing or empty text.")

    # 2. Generate embeddings
    try:
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embed_texts(texts)
    except Exception as exc:
        print("Failed to generate embeddings.")
        raise RuntimeError("Chunk embedding failed.") from exc

    # 3. Validate embedding count
    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Embedding count mismatch: expected {len(chunks)}, "
            f"received {len(embeddings)}."
        )

    # 4. Build Qdrant points
    points = []

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        if not embedding:
            raise ValueError(f"Embedding at index {index} is empty.")

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=chunk,
            )
        )

    # 5. Upsert in smaller requests to avoid timing out on large payloads.
    batch_size = 20
    try:
        for start in range(0, len(points), batch_size):
            batch = points[start:start + batch_size]
            result = qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True,
            )
            print(
                f"Ingested {min(start + len(batch), len(points))}/{len(points)} "
                f"chunks. Qdrant status: {result.status}"
            )

    except Exception as exc:
        print("Failed to upsert chunks into Qdrant.")
        raise RuntimeError("Qdrant ingestion failed.") from exc



# ─── Step 6: Retrieve ───────────────────────────────────────────────────

def retrieve(query: str, k: int = 3) -> list[dict[str, Any]]:
    """Retrieve top-k chunks for a query."""
    
    # 1. Validate inputs
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer.")

    # 2. Embed the query
    try:
        embeddings = embed_texts([query.strip()])

        if len(embeddings) != 1 or not embeddings[0]:
            raise ValueError("Failed to generate a valid query embedding.")

        query_vector = embeddings[0]

    except Exception as exc:
        print("Failed to embed retrieval query.")
        raise RuntimeError("Query embedding failed.") from exc

    # 3. Search Qdrant
    try:
        response = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=k,
            with_payload=True,
            with_vectors=False,
        )

        results: list[dict[str, Any]] = []

        # 4. Extract payload and score
        for index, point in enumerate(response.points):
            if not point.payload:
                print(f"Retrieved point at index {index} has no payload.")
                continue

            chunk = dict(point.payload)
            chunk["score"] = point.score
            results.append(chunk)

        print(f"Retrieved {len(results)} chunks for query (requested k={k}).")

        return results

    except Exception as exc:
        print("Qdrant retrieval failed.")
        raise RuntimeError("Chunk retrieval failed.") from exc


# ─── Step 7: Generate the answer ────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful assistant answering questions about a small
collection of Sherlock Holmes stories. You will be given the user's question and
several relevant excerpts. Use ONLY the provided excerpts to answer. If the
excerpts don't contain the answer, say so plainly. Cite the source (story title
+ section) in your answer."""


def answer(question: str, k: int = 3) -> dict[str, Any]:
    """End-to-end: retrieve, format context, call LLM, return result."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")

    start_time = time.perf_counter()

    # 1. Retrieve relevant chunks
    try:
        chunks = retrieve(question, k=k)
    except Exception as exc:
        print("Retrieval failed.")
        raise RuntimeError("Unable to retrieve relevant context.") from exc

    # 2. Format context and citations
    context_parts = []
    citations = []

    for index, chunk in enumerate(chunks, start=1):
        title = chunk.get("title") or chunk.get("source") or "Unknown"
        section = chunk.get("section") or "General"
        text = chunk.get("text", "")

        context_parts.append(
            f"[Source: {title} — {section}]\n{text}"
        )

        citations.append({
            "id": index,
            "title": title,
            "section": section,
            "source": chunk.get("source"),
            "score": chunk.get("score"),
        })

    context = "\n\n".join(context_parts)

    # 3. Call the LLM
    try:
        response = openai.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Context:\n{context or 'No relevant context was retrieved.'}"
                        f"\n\nQuestion:\n{question.strip()}"
                    ),
                },
            ],
            temperature=0,
        )

        llm_answer = response.choices[0].message.content

        if llm_answer is None:
            raise ValueError("The LLM returned an empty response.")

    except Exception as exc:
        print("LLM answer generation failed.")
        raise RuntimeError("Unable to generate an answer.") from exc

    # 4. Return result with latency
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "question": question.strip(),
        "answer": llm_answer.strip(),
        "citations": citations,
        "latency_ms": latency_ms,
    }


# ─── Validation harness (provided — do not modify) ──────────────────────

def validate_against(jsonl_path: Path) -> None:
    questions = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
    print(f"\n  Validating {len(questions)} questions from {jsonl_path.name}…\n")

    hits = 0
    for q in questions:
        result = answer(q["question"], k=3)
        cited_sources = {cit["source"] for cit in result["citations"]}
        source_hit = q["expected_source"] in cited_sources

        ans_lower = result["answer"].lower()
        facts_hit = sum(1 for fact in q.get("expected_facts", []) if fact.lower() in ans_lower)
        facts_total = len(q.get("expected_facts", []))

        verdict = "✓" if source_hit else "✗"
        print(f"  {verdict} {q['id']}")
        print(f"      Q: {q['question']}")
        print(f"      Cited: {', '.join(cited_sources)}")
        print(f"      Expected: {q['expected_source']}")
        print(f"      Facts matched: {facts_hit}/{facts_total}")
        print(f"      Latency: {result.get('latency_ms', '?')}ms")
        print()
        if source_hit:
            hits += 1

    print(f"  Source-match: {hits}/{len(questions)}")


# ─── CLI (provided — do not modify) ─────────────────────────────────────

def cmd_ingest() -> None:
    print("→ Loading corpus…")
    docs = load_corpus(CORPUS_DIR)
    print(f"  {len(docs)} documents loaded")

    print("→ Chunking…")
    all_chunks: list[dict[str, Any]] = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"  {doc['source']}: {len(chunks)} chunks")

    print(f"→ Total chunks: {len(all_chunks)}")
    print("→ Setting up Qdrant collection…")
    setup_collection()

    print("→ Ingesting…")
    ingest_chunks(all_chunks)
    print("\n✓ Done. Try: python mp2_rag.py ask")


def cmd_ask() -> None:
    print("Mini-RAG over the Sherlock Holmes corpus.")
    print("Type your question. Empty line or Ctrl-C to exit.\n")
    while True:
        try:
            q = input("? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not q:
            return
        result = answer(q, k=3)
        print(f"\n{result['answer']}\n")
        print("  Sources:")
        for c in result["citations"]:
            print(f"    - {c['title']} — {c['section']}")
        print(f"  Latency: {result.get('latency_ms', '?')}ms\n")


def cmd_validate() -> None:
    validate_against(DATA_DIR / "predefined_questions.jsonl")
    learner_path = DATA_DIR / "learner_questions.jsonl"
    if learner_path.exists():
        first = json.loads(learner_path.read_text().splitlines()[0])
        if not first["question"].startswith("Replace this"):
            validate_against(learner_path)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "ingest":   cmd_ingest()
    elif cmd == "ask":    cmd_ask()
    elif cmd == "validate": cmd_validate()
    else:
        print(f"Unknown command: {cmd}\n")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
