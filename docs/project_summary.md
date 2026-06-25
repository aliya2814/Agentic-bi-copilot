# Project Summary

## Problem

Business users often need fast answers to questions such as what changed, why it changed, and what actions should follow. Traditional dashboards can show metrics, but they usually require the user to know which dashboard, filter, table, or chart to inspect. General chat assistants can produce fluent summaries, but they can be difficult to trust if the path from question to evidence is unclear.

Agentic BI Copilot addresses that gap with a local, traceable BI workflow.

## Solution

The project is a business intelligence copilot that turns a natural-language question into a structured analysis pipeline. It classifies the question, queries a sample SQLite business database, runs Python calculations, retrieves relevant business documents, generates charts, and returns an evidence-based report.

The current implementation is deterministic and local. It does not require an external API key.

## How The Agent Works

The LangGraph workflow keeps a shared state object as the question moves through the pipeline:

1. The planner node determines the business intent.
2. The SQL node runs the selected read-only database query.
3. The analysis node computes broader business metrics.
4. The RAG node retrieves relevant snippets from local markdown documents.
5. The chart node generates visual artifacts.
6. The report node formats a final answer using the collected evidence.

This makes the result easier to inspect than a single black-box response.

## Tools Used

- SQLite stores the sample business database.
- pandas calculates monthly performance, category movement, inventory risk, and margin pressure.
- A read-only SQL helper runs safe canned queries.
- A keyword retrieval helper searches local business documents.
- matplotlib generates chart images.
- Streamlit provides a local UI.
- LangGraph orchestrates the workflow.
- The evaluation runner checks routing and report expectations across 15 test questions.

## Why This Is An Agentic BI System

The project is agentic because it decomposes a business question into coordinated steps with explicit state passed between nodes. Each node has a responsibility, produces evidence, and hands structured outputs to the next stage. The report is not written in isolation; it is assembled from SQL results, Python analysis, retrieved context, and chart metadata.

This is different from a static dashboard because the user can ask different questions and the system routes the work to the relevant analysis path.

## Engineering Highlights

The project demonstrates practical engineering judgment for AI-adjacent analytics by keeping the system traceable, local, modular, and easy to validate:

- It keeps evidence traceable.
- It avoids unnecessary external dependencies.
- It uses a realistic business data model.
- It separates orchestration, data access, analysis, retrieval, charting, UI, and evaluation.
- It includes a repeatable QA framework with a current 15/15 pass result.
- It is small enough to run locally but structured enough to extend.
