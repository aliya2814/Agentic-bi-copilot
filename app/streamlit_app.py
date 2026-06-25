from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.graph import run_agent  # noqa: E402


EXAMPLE_QUESTIONS = [
    "Why did sales change this month and what should we do next?",
    "Which categories grew the most?",
    "Which low stock products create the biggest inventory risk?",
    "What are the top products by revenue?",
    "What marketing campaigns affected sales?",
    "Why did margin pressure increase in June?",
]


def unique_sources(rag_context: list[dict]) -> list[str]:
    return list(dict.fromkeys(row["source"] for row in rag_context if row.get("source")))


def display_charts(chart_outputs: list[dict]) -> None:
    chart_paths = []
    if chart_outputs:
        chart_paths = [Path(chart["file_path"]) for chart in chart_outputs]
    else:
        chart_paths = sorted((ROOT_DIR / "outputs" / "charts").glob("*.png"))

    if not chart_paths:
        st.info("No charts generated yet.")
        return

    for chart_path in chart_paths:
        if chart_path.exists():
            st.image(str(chart_path), caption=chart_path.name, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Agentic BI Copilot", layout="wide")

    st.title("Agentic BI Copilot")
    st.write(
        "A local LangGraph business intelligence copilot that combines SQL, pandas analysis, "
        "keyword document retrieval, charts, and an evidence-based report."
    )

    if "question" not in st.session_state:
        st.session_state["question"] = EXAMPLE_QUESTIONS[0]

    st.sidebar.header("Example questions")
    for example in EXAMPLE_QUESTIONS:
        if st.sidebar.button(example):
            st.session_state["question"] = example

    question = st.text_area(
        "Business question",
        key="question",
        height=120,
    )

    if st.button("Run Analysis", type="primary"):
        if not question.strip():
            st.warning("Enter a business question first.")
            return

        with st.spinner("Running analysis..."):
            result = run_agent(question.strip())

        st.session_state["agent_result"] = result

    result = st.session_state.get("agent_result")
    if not result:
        return

    st.subheader("Final report")
    st.markdown(result.get("answer", ""))

    st.subheader("Routing")
    col1, col2, col3 = st.columns(3)
    col1.metric("SQL task", result.get("sql_task", ""))
    col2.metric("Answer type", result.get("answer_type", ""))
    col3.metric("Focus area", result.get("focus_area", ""))

    rag_context = result.get("rag_context", [])
    st.subheader("Retrieved document evidence")
    sources = unique_sources(rag_context)
    if sources:
        for source in sources:
            st.write(f"- {source}")
    else:
        st.write("No document evidence retrieved.")

    st.subheader("Generated charts")
    display_charts(result.get("chart_outputs", []))


if __name__ == "__main__":
    main()
