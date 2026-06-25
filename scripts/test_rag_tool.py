from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.rag_tool import retrieve_relevant_context  # noqa: E402


QUERIES = [
    "Why did margin pressure increase in June?",
    "Which products should be prioritised for reorder?",
    "What marketing campaigns affected sales?",
    "How should low stock products be handled?",
]


def shorten(text: str, length: int = 220) -> str:
    compact = " ".join(text.split())
    if len(compact) <= length:
        return compact
    return f"{compact[:length].rstrip()}..."


def main() -> None:
    for query in QUERIES:
        print(f"Query: {query}")
        print("-" * (len(query) + 7))
        results = retrieve_relevant_context(query, top_k=3)
        for index, result in enumerate(results, start=1):
            print(f"{index}. {result['source']} | score={result['score']}")
            print(f"   {shorten(result['chunk'])}")
        print()


if __name__ == "__main__":
    main()
