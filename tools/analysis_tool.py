from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "processed" / "business.db"


def _ensure_database_exists() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {DB_PATH}. "
            "Run `python scripts/create_sample_db.py` before using the analysis tool."
        )


def _connect_read_only() -> sqlite3.Connection:
    _ensure_database_exists()
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def _read_sql(query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with _connect_read_only() as conn:
        return pd.read_sql_query(query, conn, params=params)


def _round_money(value: Any) -> float:
    return round(float(value or 0), 2)


def _round_pct(value: Any) -> float:
    return round(float(value or 0), 2)


def _safe_pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return _round_pct(((current - previous) / previous) * 100)


def _to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for record in df.to_dict(orient="records"):
        cleaned = {}
        for key, value in record.items():
            if pd.isna(value):
                cleaned[key] = None
            elif isinstance(value, float):
                cleaned[key] = round(value, 2)
            elif hasattr(value, "item"):
                cleaned[key] = value.item()
            else:
                cleaned[key] = value
        records.append(cleaned)
    return records


def _monthly_sales_df() -> pd.DataFrame:
    return _read_sql(
        """
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            COUNT(DISTINCT o.order_id) AS order_count,
            SUM(oi.quantity) AS units_sold,
            SUM(oi.line_revenue) AS revenue,
            SUM(oi.line_cost) AS cost,
            SUM(oi.line_margin) AS gross_margin
        FROM orders AS o
        JOIN order_items AS oi ON oi.order_id = o.order_id
        GROUP BY strftime('%Y-%m', o.order_date)
        ORDER BY month
        """
    )


def _latest_previous_months() -> tuple[str, str]:
    monthly = _monthly_sales_df()
    if len(monthly) < 2:
        raise ValueError("At least two months of order data are required for analysis.")
    return str(monthly.iloc[-1]["month"]), str(monthly.iloc[-2]["month"])


def analyse_monthly_sales_performance() -> dict:
    monthly = _monthly_sales_df()
    if len(monthly) < 2:
        raise ValueError("At least two months of order data are required for monthly performance analysis.")

    latest = monthly.iloc[-1]
    previous = monthly.iloc[-2]
    latest_revenue = _round_money(latest["revenue"])
    previous_revenue = _round_money(previous["revenue"])
    revenue_change = _round_money(latest_revenue - previous_revenue)

    return {
        "latest_month": str(latest["month"]),
        "previous_month": str(previous["month"]),
        "latest_month_revenue": latest_revenue,
        "previous_month_revenue": previous_revenue,
        "revenue_change_amount": revenue_change,
        "revenue_change_pct": _safe_pct_change(latest_revenue, previous_revenue),
        "latest_month_order_count": int(latest["order_count"]),
        "previous_month_order_count": int(previous["order_count"]),
        "latest_month_gross_margin": _round_money(latest["gross_margin"]),
        "previous_month_gross_margin": _round_money(previous["gross_margin"]),
        "latest_month_gross_margin_pct": _round_pct((latest["gross_margin"] / latest["revenue"]) * 100),
        "previous_month_gross_margin_pct": _round_pct((previous["gross_margin"] / previous["revenue"]) * 100),
    }


def analyse_category_performance() -> dict:
    latest_month, previous_month = _latest_previous_months()
    category_df = _read_sql(
        """
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            p.category,
            SUM(oi.quantity) AS units_sold,
            SUM(oi.line_revenue) AS revenue,
            SUM(oi.line_margin) AS gross_margin
        FROM orders AS o
        JOIN order_items AS oi ON oi.order_id = o.order_id
        JOIN products AS p ON p.product_id = oi.product_id
        WHERE strftime('%Y-%m', o.order_date) IN (?, ?)
        GROUP BY strftime('%Y-%m', o.order_date), p.category
        """,
        (latest_month, previous_month),
    )

    latest = category_df[category_df["month"] == latest_month].copy()
    previous = category_df[category_df["month"] == previous_month].copy()

    latest = latest.rename(columns={"revenue": "latest_revenue", "units_sold": "latest_units_sold"})
    previous = previous.rename(columns={"revenue": "previous_revenue", "units_sold": "previous_units_sold"})

    comparison = pd.merge(
        latest[["category", "latest_units_sold", "latest_revenue"]],
        previous[["category", "previous_units_sold", "previous_revenue"]],
        on="category",
        how="outer",
    ).fillna(0)

    comparison["change_amount"] = comparison["latest_revenue"] - comparison["previous_revenue"]
    comparison["change_pct"] = comparison.apply(
        lambda row: _safe_pct_change(row["latest_revenue"], row["previous_revenue"]),
        axis=1,
    )

    latest_summary = latest[["category", "latest_units_sold", "latest_revenue"]].sort_values(
        "latest_revenue", ascending=False
    )
    previous_summary = previous[["category", "previous_units_sold", "previous_revenue"]].sort_values(
        "previous_revenue", ascending=False
    )
    changes = comparison.sort_values("change_amount", ascending=False)
    declining_categories = comparison[comparison["change_amount"] < 0].sort_values("change_amount")
    growing_categories = comparison[comparison["change_amount"] > 0].sort_values("change_amount", ascending=False)

    return {
        "latest_month": latest_month,
        "previous_month": previous_month,
        "latest_month_revenue_by_category": _to_records(latest_summary),
        "previous_month_revenue_by_category": _to_records(previous_summary),
        "category_changes": _to_records(changes),
        "top_declining_categories": _to_records(declining_categories.head(3)),
        "top_growing_categories": _to_records(growing_categories.head(3)),
    }


def analyse_margin_pressure() -> dict:
    df = _read_sql(
        """
        SELECT
            spc.change_id,
            spc.change_date,
            spc.old_cost_price,
            spc.new_cost_price,
            spc.change_pct,
            spc.reason,
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            p.sell_price,
            s.supplier_name,
            COALESCE(SUM(CASE WHEN o.order_date >= spc.change_date THEN oi.quantity ELSE 0 END), 0) AS units_sold_after_change,
            COALESCE(SUM(CASE WHEN o.order_date >= spc.change_date THEN oi.line_revenue ELSE 0 END), 0) AS revenue_after_change
        FROM supplier_price_changes AS spc
        JOIN products AS p ON p.product_id = spc.product_id
        JOIN suppliers AS s ON s.supplier_id = spc.supplier_id
        LEFT JOIN order_items AS oi ON oi.product_id = p.product_id
        LEFT JOIN orders AS o ON o.order_id = oi.order_id
        GROUP BY
            spc.change_id,
            spc.change_date,
            spc.old_cost_price,
            spc.new_cost_price,
            spc.change_pct,
            spc.reason,
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            p.sell_price,
            s.supplier_name
        """
    )

    if df.empty:
        return {
            "price_increase_count": 0,
            "products_with_supplier_price_increases": [],
            "categories_most_affected": [],
            "top_products_with_margin_pressure": [],
        }

    df["old_gross_margin_pct"] = ((df["sell_price"] - df["old_cost_price"]) / df["sell_price"]) * 100
    df["new_gross_margin_pct"] = ((df["sell_price"] - df["new_cost_price"]) / df["sell_price"]) * 100
    df["gross_margin_pct_change"] = df["new_gross_margin_pct"] - df["old_gross_margin_pct"]
    df["gross_margin_pct_reduced"] = df["gross_margin_pct_change"] < 0
    df["cost_increase_per_unit"] = df["new_cost_price"] - df["old_cost_price"]
    df["estimated_margin_impact"] = df["cost_increase_per_unit"] * df["units_sold_after_change"]

    product_columns = [
        "sku",
        "product_name",
        "category",
        "supplier_name",
        "change_date",
        "change_pct",
        "old_gross_margin_pct",
        "new_gross_margin_pct",
        "gross_margin_pct_change",
        "gross_margin_pct_reduced",
        "units_sold_after_change",
        "estimated_margin_impact",
    ]
    product_pressure = df.sort_values(
        ["estimated_margin_impact", "change_pct"], ascending=[False, False]
    )[product_columns]

    categories = (
        df.groupby("category", as_index=False)
        .agg(
            products_affected=("product_id", "count"),
            average_cost_increase_pct=("change_pct", "mean"),
            average_gross_margin_pct_change=("gross_margin_pct_change", "mean"),
            estimated_margin_impact=("estimated_margin_impact", "sum"),
        )
        .sort_values("estimated_margin_impact", ascending=False)
    )

    return {
        "price_increase_count": int(len(df)),
        "products_with_supplier_price_increases": _to_records(product_pressure.head(10)),
        "categories_most_affected": _to_records(categories.head(5)),
        "top_products_with_margin_pressure": _to_records(product_pressure.head(5)),
    }


def analyse_inventory_risk() -> dict:
    df = _read_sql(
        """
        SELECT
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            i.stock_qty,
            i.reorder_level,
            SUM(oi.quantity) AS units_sold,
            SUM(oi.line_revenue) AS revenue,
            SUM(oi.line_margin) AS gross_margin
        FROM products AS p
        JOIN inventory AS i ON i.product_id = p.product_id
        JOIN order_items AS oi ON oi.product_id = p.product_id
        WHERE i.stock_qty <= i.reorder_level
        GROUP BY
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            i.stock_qty,
            i.reorder_level
        """
    )

    if df.empty:
        return {
            "high_revenue_low_stock_count": 0,
            "total_revenue_at_risk": 0.0,
            "top_inventory_risk_products": [],
        }

    df["stock_gap"] = df["reorder_level"] - df["stock_qty"]
    df["stock_gap_pct"] = (df["stock_gap"] / df["reorder_level"]) * 100
    df["estimated_revenue_at_risk"] = df["revenue"] * (df["stock_gap"] / df["reorder_level"]).clip(lower=0, upper=1)
    df["risk_score"] = df["estimated_revenue_at_risk"] / 1000
    df["risk_level"] = pd.cut(
        df["risk_score"],
        bins=[-1, 25, 100, float("inf")],
        labels=["Medium", "High", "Critical"],
    ).astype(str)

    risk_products = df.sort_values("estimated_revenue_at_risk", ascending=False)[
        [
            "sku",
            "product_name",
            "category",
            "stock_qty",
            "reorder_level",
            "stock_gap",
            "stock_gap_pct",
            "units_sold",
            "revenue",
            "estimated_revenue_at_risk",
            "risk_level",
        ]
    ]

    return {
        "high_revenue_low_stock_count": int(len(df)),
        "total_revenue_at_risk": _round_money(df["estimated_revenue_at_risk"].sum()),
        "top_inventory_risk_products": _to_records(risk_products.head(10)),
    }


def generate_business_recommendations() -> dict:
    monthly = analyse_monthly_sales_performance()
    category = analyse_category_performance()
    margin = analyse_margin_pressure()
    inventory = analyse_inventory_risk()

    top_growing = category["top_growing_categories"][0] if category["top_growing_categories"] else None
    top_declining = category["top_declining_categories"][0] if category["top_declining_categories"] else None
    top_margin_pressure = (
        margin["top_products_with_margin_pressure"][0] if margin["top_products_with_margin_pressure"] else None
    )
    top_inventory_risk = (
        inventory["top_inventory_risk_products"][0] if inventory["top_inventory_risk_products"] else None
    )

    direction = "up" if monthly["revenue_change_amount"] >= 0 else "down"
    executive_summary = (
        f"Latest month revenue was ${monthly['latest_month_revenue']:,.2f}, "
        f"{direction} ${abs(monthly['revenue_change_amount']):,.2f} "
        f"({monthly['revenue_change_pct']:.2f}%) versus {monthly['previous_month']}. "
        f"Gross margin was ${monthly['latest_month_gross_margin']:,.2f}."
    )

    key_findings = [
        (
            f"Orders changed from {monthly['previous_month_order_count']} to "
            f"{monthly['latest_month_order_count']} month over month."
        )
    ]
    if top_growing:
        key_findings.append(
            f"{top_growing['category']} was the strongest growing category, "
            f"adding ${top_growing['change_amount']:,.2f} in revenue."
        )
    if top_declining:
        key_findings.append(
            f"{top_declining['category']} was the weakest category, "
            f"changing by ${top_declining['change_amount']:,.2f}."
        )
    if top_margin_pressure:
        key_findings.append(
            f"{top_margin_pressure['product_name']} has margin pressure from a "
            f"{top_margin_pressure['change_pct']:.2f}% supplier cost increase."
        )
    if top_inventory_risk:
        key_findings.append(
            f"{top_inventory_risk['product_name']} is a stock risk with "
            f"{top_inventory_risk['stock_qty']} units on hand against a reorder level of "
            f"{top_inventory_risk['reorder_level']}."
        )

    recommended_actions = [
        "Prioritise replenishment for high-revenue products below reorder level.",
        "Review pricing or supplier terms for products with recent cost increases.",
        "Protect spend behind growing categories while diagnosing declining category demand.",
    ]
    if top_inventory_risk:
        recommended_actions.insert(
            0,
            f"Reorder {top_inventory_risk['product_name']} or shift available stock to channels with strongest demand.",
        )

    return {
        "executive_summary": executive_summary,
        "key_findings": key_findings,
        "recommended_actions": recommended_actions,
        "evidence": {
            "monthly_sales_performance": monthly,
            "top_growing_categories": category["top_growing_categories"],
            "top_declining_categories": category["top_declining_categories"],
            "categories_most_affected_by_cost_increases": margin["categories_most_affected"],
            "top_margin_pressure_products": margin["top_products_with_margin_pressure"],
            "top_inventory_risk_products": inventory["top_inventory_risk_products"],
            "total_revenue_at_risk": inventory["total_revenue_at_risk"],
        },
    }
