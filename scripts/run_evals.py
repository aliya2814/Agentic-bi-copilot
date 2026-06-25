from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.graph import run_agent  # noqa: E402


EVALS_PATH = ROOT_DIR / "evals" / "test_questions.json"
OUTPUT_DIR = ROOT_DIR / "outputs" / "evals"
RESULTS_PATH = OUTPUT_DIR / "evaluation_results.json"
SUMMARY_PATH = OUTPUT_DIR / "evaluation_summary.md"


def _contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def _run_single_eval(test_case: dict[str, Any]) -> dict[str, Any]:
    result = run_agent(test_case["question"])
    answer = result.get("answer", "")

    missing_keywords = [
        keyword
        for keyword in test_case.get("expected_keywords_in_answer", [])
        if not _contains_keyword(answer, keyword)
    ]

    checks = {
        "answer_type": result.get("answer_type") == test_case["expected_answer_type"],
        "sql_task": result.get("sql_task") == test_case["expected_sql_task"],
        "focus_area_keyword": _contains_keyword(
            result.get("focus_area", ""),
            test_case["expected_focus_area_keyword"],
        ),
        "answer_keywords": not missing_keywords,
    }

    return {
        "question": test_case["question"],
        "passed": all(checks.values()),
        "checks": checks,
        "expected": {
            "answer_type": test_case["expected_answer_type"],
            "sql_task": test_case["expected_sql_task"],
            "focus_area_keyword": test_case["expected_focus_area_keyword"],
            "keywords_in_answer": test_case.get("expected_keywords_in_answer", []),
        },
        "actual": {
            "answer_type": result.get("answer_type"),
            "sql_task": result.get("sql_task"),
            "focus_area": result.get("focus_area"),
        },
        "missing_keywords": missing_keywords,
        "answer_preview": answer.splitlines()[:8],
    }


def _write_outputs(results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Evaluation Summary",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Total tests: {summary['total_tests']}",
        f"- Passed tests: {summary['passed_tests']}",
        f"- Failed tests: {summary['failed_tests']}",
        f"- Pass rate: {summary['pass_rate_pct']:.2f}%",
        "",
        "| Status | Question | Answer Type | SQL Task | Missing Keywords |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        missing = ", ".join(result["missing_keywords"]) if result["missing_keywords"] else "-"
        lines.append(
            "| {status} | {question} | {answer_type} | {sql_task} | {missing} |".format(
                status=status,
                question=result["question"].replace("|", "\\|"),
                answer_type=result["actual"]["answer_type"],
                sql_task=result["actual"]["sql_task"],
                missing=missing.replace("|", "\\|"),
            )
        )

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    test_cases = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    results = []

    for index, test_case in enumerate(test_cases, start=1):
        result = _run_single_eval(test_case)
        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {index:02d}. {result['question']}")
        print(f"  answer_type: {result['actual']['answer_type']} expected {result['expected']['answer_type']}")
        print(f"  sql_task: {result['actual']['sql_task']} expected {result['expected']['sql_task']}")
        if result["missing_keywords"]:
            print(f"  missing_keywords: {', '.join(result['missing_keywords'])}")

    total_tests = len(results)
    passed_tests = sum(1 for result in results if result["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate_pct = (passed_tests / total_tests) * 100 if total_tests else 0.0
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "pass_rate_pct": pass_rate_pct,
    }
    _write_outputs(results, summary)

    print("=" * 80)
    print("Evaluation summary")
    print(f"total tests: {total_tests}")
    print(f"passed tests: {passed_tests}")
    print(f"failed tests: {failed_tests}")
    print(f"pass rate: {pass_rate_pct:.2f}%")
    print(f"results json: {RESULTS_PATH}")
    print(f"summary markdown: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
