from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "processed" / "business.db"
CHART_OUTPUT_DIR = ROOT_DIR / "outputs" / "charts"


def ensure_chart_output_dir() -> Path:
    CHART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return CHART_OUTPUT_DIR


def _ensure_database_exists() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {DB_PATH}. "
            "Run `python scripts/create_sample_db.py` before generating charts."
        )


def _fetch_rows(query: str, params: tuple[Any, ...] = ()) -> list[dict]:
    _ensure_database_exists()
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def _currency_axis(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(lambda value, _position: f"${value / 1000:,.0f}k")


def _save_chart(file_name: str) -> Path:
    output_dir = ensure_chart_output_dir()
    file_path = output_dir / file_name
    plt.tight_layout()
    plt.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close()
    return file_path


def create_monthly_revenue_chart() -> dict:
    rows = _fetch_rows(
        """
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            SUM(oi.line_revenue) AS revenue,
            SUM(oi.line_margin) AS gross_margin
        FROM orders AS o
        JOIN order_items AS oi ON oi.order_id = o.order_id
        GROUP BY strftime('%Y-%m', o.order_date)
        ORDER BY month
        """
    )

    months = [row["month"] for row in rows]
    revenue = [row["revenue"] for row in rows]
    gross_margin = [row["gross_margin"] for row in rows]

    plt.figure(figsize=(10, 5))
    plt.plot(months, revenue, marker="o", linewidth=2.2, color="#2563eb", label="Revenue")
    plt.plot(months, gross_margin, marker="o", linewidth=2.0, color="#16a34a", label="Gross margin")
    ax = plt.gca()
    _currency_axis(ax)
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", alpha=0.25)
    plt.legend()

    file_path = _save_chart("monthly_revenue_trend.png")
    return {
        "chart_name": "Monthly Revenue Trend",
        "file_path": str(file_path),
        "description": "Revenue and gross margin by month for the last 12 months.",
    }


def create_category_revenue_change_chart() -> dict:
    month_rows = _fetch_rows(
        """
        SELECT strftime('%Y-%m', order_date) AS month
        FROM orders
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month DESC
        LIMIT 2
        """
    )
    if len(month_rows) < 2:
        raise ValueError("At least two months of order data are required for category revenue change chart.")

    latest_month = month_rows[0]["month"]
    previous_month = month_rows[1]["month"]
    rows = _fetch_rows(
        """
        SELECT
            p.category,
            SUM(CASE WHEN strftime('%Y-%m', o.order_date) = ? THEN oi.line_revenue ELSE 0 END) AS latest_revenue,
            SUM(CASE WHEN strftime('%Y-%m', o.order_date) = ? THEN oi.line_revenue ELSE 0 END) AS previous_revenue
        FROM orders AS o
        JOIN order_items AS oi ON oi.order_id = o.order_id
        JOIN products AS p ON p.product_id = oi.product_id
        WHERE strftime('%Y-%m', o.order_date) IN (?, ?)
        GROUP BY p.category
        ORDER BY p.category
        """,
        (latest_month, previous_month, latest_month, previous_month),
    )

    categories = [row["category"] for row in rows]
    changes = [row["latest_revenue"] - row["previous_revenue"] for row in rows]
    colors = ["#16a34a" if value >= 0 else "#dc2626" for value in changes]

    plt.figure(figsize=(10, 5))
    plt.bar(categories, changes, color=colors)
    ax = plt.gca()
    _currency_axis(ax)
    plt.axhline(0, color="#111827", linewidth=0.8)
    plt.title(f"Category Revenue Change: {previous_month} to {latest_month}")
    plt.xlabel("Category")
    plt.ylabel("Revenue change")
    plt.xticks(rotation=25, ha="right")
    plt.grid(axis="y", alpha=0.25)

    file_path = _save_chart("category_revenue_change.png")
    return {
        "chart_name": "Category Revenue Change",
        "file_path": str(file_path),
        "description": f"Revenue change by category from {previous_month} to {latest_month}.",
    }


def create_inventory_risk_chart() -> dict:
    rows = _fetch_rows(
        """
        SELECT
            p.product_name,
            p.category,
            i.stock_qty,
            i.reorder_level,
            SUM(oi.line_revenue) AS revenue,
            (i.reorder_level - i.stock_qty) AS stock_gap,
            SUM(oi.line_revenue) *
                CASE
                    WHEN i.reorder_level = 0 THEN 0
                    ELSE MIN(MAX((i.reorder_level - i.stock_qty) * 1.0 / i.reorder_level, 0), 1)
                END AS estimated_revenue_at_risk
        FROM products AS p
        JOIN inventory AS i ON i.product_id = p.product_id
        JOIN order_items AS oi ON oi.product_id = p.product_id
        WHERE i.stock_qty <= i.reorder_level
        GROUP BY
            p.product_id,
            p.product_name,
            p.category,
            i.stock_qty,
            i.reorder_level
        ORDER BY estimated_revenue_at_risk DESC
        LIMIT 10
        """
    )

    labels = [f"{row['product_name']}\n{row['category']}" for row in rows]
    risk_values = [row["estimated_revenue_at_risk"] for row in rows]

    plt.figure(figsize=(10, 7))
    plt.barh(labels, risk_values, color="#f97316")
    ax = plt.gca()
    ax.xaxis.set_major_formatter(lambda value, _position: f"${value / 1000:,.0f}k")
    plt.title("Top Inventory Risk Products")
    plt.xlabel("Estimated revenue at risk")
    plt.ylabel("Product")
    plt.gca().invert_yaxis()
    plt.grid(axis="x", alpha=0.25)

    file_path = _save_chart("inventory_risk_top_products.png")
    return {
        "chart_name": "Inventory Risk Top Products",
        "file_path": str(file_path),
        "description": "Top low-stock products ranked by estimated revenue at risk.",
    }


def generate_all_charts() -> list[dict]:
    return [
        create_monthly_revenue_chart(),
        create_category_revenue_change_chart(),
        create_inventory_risk_chart(),
    ]
