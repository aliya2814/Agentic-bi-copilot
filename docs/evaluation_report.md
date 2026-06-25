# Evaluation Report

## Current Result

The current evaluation suite contains 15 questions and passes all 15.

- Total tests: 15
- Passed tests: 15
- Failed tests: 0
- Pass rate: 100.00%

The latest generated outputs are stored in:

- `outputs/evals/evaluation_results.json`
- `outputs/evals/evaluation_summary.md`

## What Was Tested

The evaluation suite runs each question in `evals/test_questions.json` through `run_agent(question)` and checks:

- Actual `answer_type` matches the expected answer type.
- Actual `sql_task` matches the expected SQL task.
- The expected focus-area keyword appears in the routed focus area.
- Expected keywords appear in the final answer text.

The questions cover:

- Category growth
- Inventory risk
- Margin pressure
- Top products
- Monthly summaries
- General business reviews

## Why Routing Evaluation Matters

Routing is the first major decision in this BI workflow. If the planner maps a question to the wrong answer type or SQL task, every downstream step can still run successfully while producing the wrong kind of business answer.

For example, a margin-pressure question should not be treated as a top-products question, and an inventory-risk question should use the low-stock high-revenue SQL path. The evaluation suite provides a regression harness for these decisions.

## Limitations

The current evaluation is intentionally lightweight. It verifies routing and expected answer content, but it does not yet prove every numeric value in the report is correct.

Current limitations:

- Keyword checks can miss subtle answer quality issues.
- Numeric values are not asserted field by field.
- Chart files are not validated beyond being produced by the graph.
- Retrieved document snippets are not scored by human relevance.
- The suite uses a fixed synthetic dataset, so it does not test real-world data drift.

## Future Evaluation Improvements

Useful next steps:

- Add numeric assertions for revenue, margin, category changes, and inventory risk.
- Verify chart files exist and are refreshed during evaluation.
- Add negative tests for ambiguous or unsupported questions.
- Add document retrieval expectations by source filename.
- Add regression tests for report section structure.
- Track evaluation history over time to detect quality drift.
