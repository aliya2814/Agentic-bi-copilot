from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.graph import run_agent  # noqa: E402


QUESTIONS = [
    "Which categories grew the most?",
    "Which low stock products create the biggest inventory risk?",
    "Why did margin pressure increase in June?",
    "What are the top products by revenue?",
    "Why did sales change this month and what should we do next?",
]


def first_five_lines(text: str) -> list[str]:
    return text.splitlines()[:5]


def main() -> None:
    for question in QUESTIONS:
        result = run_agent(question)
        print("=" * 80)
        print(f"question: {question}")
        print(f"sql_task: {result['sql_task']}")
        print(f"answer_type: {result['answer_type']}")
        print(f"focus_area: {result['focus_area']}")
        print("first_5_answer_lines:")
        for line in first_five_lines(result["answer"]):
            print(f"  {line}")
        print()


if __name__ == "__main__":
    main()
