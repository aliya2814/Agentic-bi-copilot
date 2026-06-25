# Architecture

Agentic BI Copilot is intended to become a LangGraph-based multi-agent business intelligence workflow. The current repository only contains a minimal runnable graph. This document describes the future target architecture so implementation can grow in small, testable steps.

## Future Workflow

```text
User Question
-> Planner Agent
-> SQL Agent
-> Python Analysis Tool
-> RAG Agent
-> Critic Agent
-> Report Agent
```

## Stage Responsibilities

### User Question

The user asks a business question in natural language, such as:

```text
Why did sales drop this month?
```

The question should be preserved in graph state so each downstream stage can reference the original intent.

### Planner Agent

The planner converts the user question into a structured analysis plan. It should identify:

- The business metric being investigated.
- Relevant time periods, filters, and segments.
- Data needed from SQL tables.
- Any supporting documents that may be useful.
- The expected final output format.

### SQL Agent

The SQL agent turns the plan into one or more safe SQL queries against approved data sources. It should return query text, result summaries, and any assumptions about tables or filters.

For the MVP, this should use a local sample database rather than a production database.

### Python Analysis Tool

The Python analysis tool receives structured query results and performs calculations that are easier outside SQL, such as:

- Month-over-month changes.
- Segment contribution analysis.
- Ranking and outlier checks.
- Data quality checks.
- Chart-ready transformations.

The tool should return computed metrics and intermediate tables that can be cited by later stages.

### RAG Agent

The RAG agent retrieves relevant context from local documents, such as business definitions, KPI notes, product launch dates, pricing changes, or campaign summaries.

The RAG output should include document snippets, source names, and relevance notes.

### Critic Agent

The critic reviews the evidence before the final report is written. It should check:

- Whether the SQL results answer the original question.
- Whether calculations are consistent with the plan.
- Whether retrieved documents support or conflict with the data.
- Whether important uncertainty or missing data should be called out.

The critic should not create new conclusions without evidence.

### Report Agent

The report agent produces the final evidence-based answer. It should include:

- A concise executive summary.
- Key metrics and drivers.
- Chart references when available.
- Supporting evidence from SQL, Python analysis, and retrieved documents.
- Caveats and recommended next steps.

## State Design

The graph state should eventually carry structured fields such as:

- `question`
- `plan`
- `sql_queries`
- `sql_results`
- `analysis_results`
- `retrieved_context`
- `critique`
- `charts`
- `final_report`

The current skeleton only uses `question`, `plan`, and `answer` to keep the graph easy to run while the project foundation is being built.

## Implementation Notes

- Add one capability at a time.
- Keep every node testable without a UI.
- Prefer local sample data before external services.
- Keep external service credentials optional for local development.
- Make evidence explicit in graph state so the final report is auditable.
