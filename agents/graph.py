from __future__ import annotations

import sys
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.analysis_tool import generate_business_recommendations  # noqa: E402
from tools.chart_tool import generate_all_charts  # noqa: E402
from tools.sql_tool import (  # noqa: E402
    get_low_stock_high_revenue_products,
    get_monthly_sales_summary,
    get_top_products_by_revenue,
)
from tools.rag_tool import retrieve_relevant_context  # noqa: E402


class AgentState(TypedDict):
    question: str
    plan: str
    sql_task: str
    answer_type: str
    focus_area: str
    sql_result: list[dict]
    analysis_result: dict
    rag_context: list[dict]
    chart_outputs: list[dict]
    answer: str


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def planner_node(state: AgentState) -> AgentState:
    question = state["question"]
    question_lower = question.lower()

    if _contains_any(question_lower, ["low stock", "inventory risk", "reorder", "stock risk"]):
        sql_task = "low_stock_high_revenue"
        answer_type = "inventory_risk"
        focus_area = "high revenue products below reorder level"
    elif _contains_any(question_lower, ["margin", "cost increase", "supplier price", "pressure"]):
        sql_task = "monthly_sales_summary"
        answer_type = "margin_pressure"
        focus_area = "supplier cost increases and gross margin pressure"
    elif _contains_any(question_lower, ["top products", "revenue products", "best products"]):
        sql_task = "top_products_by_revenue"
        answer_type = "top_products"
        focus_area = "top products by revenue"
    elif _contains_any(question_lower, ["category", "categories", "grew", "growth", "growing", "declined", "decline"]):
        sql_task = "monthly_sales_summary"
        answer_type = "category_growth"
        focus_area = "category revenue growth and decline"
    elif _contains_any(question_lower, ["sales change", "this month", "monthly sales", "trend"]):
        sql_task = "monthly_sales_summary"
        answer_type = "monthly_summary"
        focus_area = "monthly sales performance"
    else:
        sql_task = "monthly_sales_summary"
        answer_type = "general_business_review"
        focus_area = "overall business performance"

    return {
        **state,
        "plan": (
            f"Plan: answer the business question with answer type `{answer_type}`, "
            f"focus area `{focus_area}`, and SQL task `{sql_task}`. Question: {question}"
        ),
        "sql_task": sql_task,
        "answer_type": answer_type,
        "focus_area": focus_area,
    }


def sql_node(state: AgentState) -> AgentState:
    sql_task = state["sql_task"]

    if sql_task == "top_products_by_revenue":
        sql_result = get_top_products_by_revenue(10)
    elif sql_task == "monthly_sales_summary":
        sql_result = get_monthly_sales_summary()
    elif sql_task == "low_stock_high_revenue":
        sql_result = get_low_stock_high_revenue_products(10)
    else:
        raise ValueError(f"Unknown SQL task: {sql_task}")

    return {
        **state,
        "sql_result": sql_result,
    }


def analysis_node(state: AgentState) -> AgentState:
    return {
        **state,
        "analysis_result": generate_business_recommendations(),
    }


def rag_node(state: AgentState) -> AgentState:
    return {
        **state,
        "rag_context": retrieve_relevant_context(state["question"], top_k=5),
    }


def chart_node(state: AgentState) -> AgentState:
    return {
        **state,
        "chart_outputs": generate_all_charts(),
    }


def _sql_task_label(sql_task: str) -> str:
    labels = {
        "top_products_by_revenue": "top products by revenue",
        "monthly_sales_summary": "monthly sales summary",
        "low_stock_high_revenue": "low-stock high-revenue products",
    }
    return labels.get(sql_task, sql_task)


def _shorten(text: str, length: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= length:
        return compact
    return f"{compact[:length].rstrip()}..."


def _format_currency(value: float | int | None) -> str:
    return f"${float(value or 0):,.2f}"


def _format_pct(value: float | int | None) -> str:
    return f"{float(value or 0):,.2f}%"


def _document_source_line(rag_context: list[dict]) -> str:
    if not rag_context:
        return "- Document retrieval: no matching document context found."
    sources = ", ".join(dict.fromkeys(row["source"] for row in rag_context))
    return f"- Document retrieval: retrieved {len(rag_context)} chunks from {sources}."


def _chart_lines(chart_outputs: list[dict], chart_names: list[str] | None = None) -> list[str]:
    if chart_names is None:
        selected_charts = chart_outputs
    else:
        selected_charts = [chart for chart in chart_outputs if chart["chart_name"] in chart_names]

    lines = ["", "Charts generated"]
    if selected_charts:
        lines.extend(f"- {chart['chart_name']}: {chart['file_path']}" for chart in selected_charts)
    else:
        lines.append("- No focused chart generated for this answer type.")
    return lines


def _format_document_context(rag_context: list[dict]) -> list[str]:
    lines = ["", "Document context"]
    if rag_context:
        for context in rag_context[:3]:
            lines.append(f"- {context['source']}: {_shorten(context['chunk'])}")
    else:
        lines.append("- No matching document context found.")
    return lines


def _format_category_growth_report(state: AgentState) -> str:
    analysis_result = state["analysis_result"]
    evidence = analysis_result["evidence"]
    monthly = evidence["monthly_sales_performance"]
    growing_categories = evidence["top_growing_categories"]
    declining_categories = evidence["top_declining_categories"]
    rag_context = state["rag_context"]
    chart_outputs = state["chart_outputs"]

    lines = [
        "Category growth",
        f"Latest month: {monthly['latest_month']}; previous month: {monthly['previous_month']}.",
        "",
        "Top growing categories",
    ]
    if growing_categories:
        for row in growing_categories:
            lines.append(
                f"- {row['category']}: {_format_currency(row['change_amount'])} "
                f"({_format_pct(row['change_pct'])}) increase."
            )
    else:
        lines.append("- No categories grew month over month.")

    lines.extend(["", "Top declining categories"])
    if declining_categories:
        for row in declining_categories:
            lines.append(
                f"- {row['category']}: {_format_currency(row['change_amount'])} "
                f"({_format_pct(row['change_pct'])}) decline."
            )
    else:
        lines.append("- No categories declined month over month.")

    interpretation = "Category growth was broad-based across the latest month."
    if growing_categories:
        interpretation = (
            f"{growing_categories[0]['category']} led category growth, adding "
            f"{_format_currency(growing_categories[0]['change_amount'])} versus the previous month."
        )

    lines.extend(
        [
            "",
            "Business interpretation",
            interpretation,
            "",
            "Recommended actions",
            "- Keep marketing and merchandising support behind the fastest-growing categories.",
            "- Compare campaign spend against the category revenue change chart before increasing discounts.",
            "- Review slower categories separately before shifting budget away from them.",
            "",
            "Evidence",
            f"- SQL: ran the {_sql_task_label(state['sql_task'])} query against business.db.",
            "- Python analysis: compared category revenue for latest month versus previous month.",
            _document_source_line(rag_context),
        ]
    )
    lines.extend(_chart_lines(chart_outputs, ["Category Revenue Change"]))
    return "\n".join(lines)


def _format_inventory_risk_report(state: AgentState) -> str:
    evidence = state["analysis_result"]["evidence"]
    inventory_risks = evidence["top_inventory_risk_products"]
    rag_context = state["rag_context"]
    chart_outputs = state["chart_outputs"]

    lines = [
        "Inventory risk",
        f"Total estimated revenue at risk: {_format_currency(evidence['total_revenue_at_risk'])}.",
        "",
        "High-revenue low-stock products",
    ]
    for row in inventory_risks[:5]:
        lines.append(
            f"- {row['product_name']}: stock {row['stock_qty']} vs reorder level {row['reorder_level']}; "
            f"estimated revenue at risk {_format_currency(row['estimated_revenue_at_risk'])}."
        )

    lines.extend(
        [
            "",
            "Recommended actions",
            "- Reorder the highest revenue-at-risk products first.",
            "- Reserve scarce stock for higher-margin direct, Trade, or Retail Event channels.",
            "- Avoid promotions on constrained products until replenishment is confirmed.",
            "",
            "Evidence",
            f"- SQL: ran the {_sql_task_label(state['sql_task'])} query and returned {len(state['sql_result'])} rows.",
            "- Python analysis: ranked low-stock products by estimated revenue at risk.",
            _document_source_line(rag_context),
        ]
    )
    lines.extend(_chart_lines(chart_outputs, ["Inventory Risk Top Products"]))
    return "\n".join(lines)


def _format_margin_pressure_report(state: AgentState) -> str:
    evidence = state["analysis_result"]["evidence"]
    affected_categories = evidence["categories_most_affected_by_cost_increases"]
    pressure_products = evidence["top_margin_pressure_products"]
    rag_context = state["rag_context"]
    chart_outputs = state["chart_outputs"]

    lines = [
        "Margin pressure",
        "Supplier price increases are reducing gross margin percentage on affected products.",
        "",
        "Affected products",
    ]
    for row in pressure_products[:5]:
        lines.append(
            f"- {row['product_name']} ({row['category']}): supplier cost increase "
            f"{_format_pct(row['change_pct'])}; gross margin percentage changed by "
            f"{row['gross_margin_pct_change']:.2f} pts."
        )

    lines.extend(["", "Categories most affected"])
    for row in affected_categories[:3]:
        lines.append(
            f"- {row['category']}: {row['products_affected']} products affected; "
            f"estimated margin impact {_format_currency(row['estimated_margin_impact'])}."
        )

    lines.extend(
        [
            "",
            "Recommended actions",
            "- Review sell prices for products with recent supplier cost increases.",
            "- Negotiate supplier terms before committing to large reorders.",
            "- Use bundles or targeted promotions instead of broad discounting on pressured products.",
            "",
            "Evidence",
            f"- SQL: ran the {_sql_task_label(state['sql_task'])} query to anchor the period context.",
            "- Python analysis: compared old and new supplier costs against current sell prices.",
            _document_source_line(rag_context),
        ]
    )
    lines.extend(_chart_lines(chart_outputs, ["Monthly Revenue Trend", "Category Revenue Change"]))
    return "\n".join(lines)


def _format_top_products_report(state: AgentState) -> str:
    rows = state["sql_result"]
    rag_context = state["rag_context"]
    chart_outputs = state["chart_outputs"]

    lines = [
        "Top products by revenue",
        "Highest revenue products in the current sample database:",
        "",
        "Products",
    ]
    for index, row in enumerate(rows[:5], start=1):
        lines.append(
            f"{index}. {row['product_name']} ({row['category']}): "
            f"{_format_currency(row['revenue'])} revenue, {row['units_sold']} units sold, "
            f"{_format_currency(row['gross_margin'])} gross margin."
        )

    lines.extend(
        [
            "",
            "Recommendation",
            "- Protect availability and merchandising for these products because they drive the largest revenue contribution.",
            "- Check stock and supplier cost movement before running discounts on the top sellers.",
            "",
            "Evidence",
            f"- SQL: ran the {_sql_task_label(state['sql_task'])} query and returned {len(rows)} rows.",
            _document_source_line(rag_context),
        ]
    )
    lines.extend(_chart_lines(chart_outputs, ["Monthly Revenue Trend"]))
    return "\n".join(lines)


def _format_full_business_report(state: AgentState) -> str:
    analysis_result = state["analysis_result"]
    evidence = analysis_result["evidence"]
    monthly = evidence["monthly_sales_performance"]
    top_inventory_risks = evidence["top_inventory_risk_products"]
    top_margin_products = evidence["top_margin_pressure_products"]
    rag_context = state["rag_context"]
    chart_outputs = state["chart_outputs"]

    lines = [
        "Summary",
        analysis_result["executive_summary"],
        "",
        "Key findings",
    ]
    lines.extend(f"- {finding}" for finding in analysis_result["key_findings"])
    lines.extend(["", "Recommended actions"])
    lines.extend(f"- {action}" for action in analysis_result["recommended_actions"])
    lines.extend(
        [
            "",
            "Evidence",
            (
                f"- SQL: ran the {_sql_task_label(state['sql_task'])} query against business.db "
                f"and returned {len(state['sql_result'])} rows."
            ),
            (
                f"- Python analysis: {monthly['latest_month']} revenue was "
                f"{_format_currency(monthly['latest_month_revenue'])}, compared with "
                f"{_format_currency(monthly['previous_month_revenue'])} in {monthly['previous_month']}."
            ),
            (
                f"- Python analysis: latest gross margin was {_format_currency(monthly['latest_month_gross_margin'])} "
                f"({_format_pct(monthly['latest_month_gross_margin_pct'])})."
            ),
        ]
    )

    if top_inventory_risks:
        top_risk = top_inventory_risks[0]
        lines.append(
            f"- Python analysis: top inventory risk is {top_risk['product_name']} with {top_risk['stock_qty']} units "
            f"against reorder level {top_risk['reorder_level']}."
        )
    if top_margin_products:
        top_margin = top_margin_products[0]
        lines.append(
            f"- Python analysis: top margin pressure is {top_margin['product_name']} after supplier cost increased "
            f"{_format_pct(top_margin['change_pct'])}."
        )
    lines.append(_document_source_line(rag_context))

    lines.extend(_format_document_context(rag_context))
    lines.extend(_chart_lines(chart_outputs))
    return "\n".join(lines)


def report_node(state: AgentState) -> AgentState:
    answer_type = state["answer_type"]

    if answer_type == "category_growth":
        answer = _format_category_growth_report(state)
    elif answer_type == "inventory_risk":
        answer = _format_inventory_risk_report(state)
    elif answer_type == "margin_pressure":
        answer = _format_margin_pressure_report(state)
    elif answer_type == "top_products":
        answer = _format_top_products_report(state)
    else:
        answer = _format_full_business_report(state)

    return {
        **state,
        "answer": answer,
    }


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("sql", sql_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("rag", rag_node)
    graph.add_node("chart", chart_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "sql")
    graph.add_edge("sql", "analysis")
    graph.add_edge("analysis", "rag")
    graph.add_edge("rag", "chart")
    graph.add_edge("chart", "report")
    graph.add_edge("report", END)

    return graph.compile()


def run_agent(question: str) -> dict:
    app = build_graph()
    return app.invoke({
        "question": question,
        "plan": "",
        "sql_task": "",
        "answer_type": "",
        "focus_area": "",
        "sql_result": [],
        "analysis_result": {},
        "rag_context": [],
        "chart_outputs": [],
        "answer": "",
    })


if __name__ == "__main__":
    result = run_agent("Why did sales change this month and what should we do next?")

    print(result["answer"])
