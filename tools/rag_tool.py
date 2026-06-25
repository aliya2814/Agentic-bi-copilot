from __future__ import annotations

import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = ROOT_DIR / "data" / "documents"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "did",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "was",
    "what",
    "which",
    "why",
    "with",
}


def load_documents() -> list[dict]:
    if not DOCUMENTS_DIR.exists():
        raise FileNotFoundError(
            f"Document folder not found at {DOCUMENTS_DIR}. "
            "Create data/documents before using the RAG tool."
        )

    documents = []
    for path in sorted(DOCUMENTS_DIR.glob("*.md")):
        documents.append(
            {
                "source": path.name,
                "path": str(path),
                "text": path.read_text(encoding="utf-8"),
            }
        )
    return documents


def chunk_document(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    cleaned_text = re.sub(r"\s+", " ", text).strip()
    if not cleaned_text:
        return []

    words = cleaned_text.split()
    chunks = []
    start_word = 0
    while start_word < len(words):
        chunk_words = []
        chunk_length = 0
        end_word = start_word

        while end_word < len(words):
            next_word = words[end_word]
            next_length = chunk_length + len(next_word) + (1 if chunk_words else 0)
            if chunk_words and next_length > chunk_size:
                break
            chunk_words.append(next_word)
            chunk_length = next_length
            end_word += 1

        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)
        if end_word == len(words):
            break

        overlap_start = end_word
        overlap_length = 0
        while overlap_start > start_word and overlap_length < overlap:
            overlap_start -= 1
            overlap_length += len(words[overlap_start]) + 1
        start_word = max(overlap_start, start_word + 1)

    return chunks


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def _score_chunk(query: str, source: str, chunk: str) -> float:
    query_terms = _tokenize(query)
    if not query_terms:
        return 0.0

    searchable_text = f"{source} {chunk}".lower()
    chunk_terms = _tokenize(searchable_text)
    score = 0.0

    for term in query_terms:
        term_count = chunk_terms.count(term)
        if term_count:
            score += term_count
        if term in source.lower():
            score += 1.5

    query_phrase = " ".join(query_terms)
    if query_phrase and query_phrase in searchable_text:
        score += 5.0

    important_phrases = [
        "margin pressure",
        "supplier cost",
        "low stock",
        "reorder",
        "marketing",
        "campaign",
        "june 2026",
        "stock priority",
    ]
    for phrase in important_phrases:
        if phrase in query.lower() and phrase in searchable_text:
            score += 3.0

    return round(score, 2)


def retrieve_relevant_context(query: str, top_k: int = 5) -> list[dict]:
    if top_k < 1:
        raise ValueError("top_k must be greater than zero.")

    scored_chunks = []
    for document in load_documents():
        chunks = chunk_document(document["text"])
        for chunk_index, chunk in enumerate(chunks):
            score = _score_chunk(query, document["source"], chunk)
            if score > 0:
                scored_chunks.append(
                    {
                        "source": document["source"],
                        "chunk": chunk,
                        "score": score,
                        "chunk_index": chunk_index,
                    }
                )

    scored_chunks.sort(key=lambda row: (row["score"], row["source"]), reverse=True)
    return [
        {
            "source": row["source"],
            "chunk": row["chunk"],
            "score": row["score"],
        }
        for row in scored_chunks[:top_k]
    ]
