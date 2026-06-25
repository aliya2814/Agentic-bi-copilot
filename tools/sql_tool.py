from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "processed" / "business.db"

BLOCKED_SQL_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
)


def get_db_path() -> Path:
    return DB_PATH


def _ensure_database_exists() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {DB_PATH}. "
            "Run `python scripts/create_sample_db.py` before using the SQL tool."
        )


def _connect_read_only() -> sqlite3.Connection:
    _ensure_database_exists()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _strip_sql_comments(query: str) -> str:
    query = re.sub(r"--.*?$", " ", query, flags=re.MULTILINE)
    query = re.sub(r"/\*.*?\*/", " ", query, flags=re.DOTALL)
    return query.strip()


def _validate_read_only_select(query: str) -> str:
    if not query or not query.strip():
        raise ValueError("SQL query cannot be empty.")

    cleaned_query = _strip_sql_comments(query)
    normalized_query = cleaned_query.strip()
    query_without_trailing_semicolon = normalized_query.rstrip(";").strip()

    if not query_without_trailing_semicolon.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    if ";" in query_without_trailing_semicolon:
        raise ValueError("Only a single SELECT query is allowed.")

    blocked_pattern = r"\b(" + "|".join(BLOCKED_SQL_KEYWORDS) + r")\b"
    blocked_match = re.search(blocked_pattern, query_without_trailing_semicolon, flags=re.IGNORECASE)
    if blocked_match:
        raise ValueError(f"Blocked unsafe SQL keyword: {blocked_match.group(1).upper()}.")

    return query_without_trailing_semicolon


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _safe_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Limit must be greater than zero.")
    return min(limit, 100)


def run_read_only_query(query: str) -> list[dict]:
    safe_query = _validate_read_only_select(query)
    with _connect_read_only() as conn:
        rows = conn.execute(safe_query).fetchall()
    return _rows_to_dicts(rows)


def get_database_schema() -> dict:
    with _connect_read_only() as conn:
        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        schema = {}
        for table_row in table_rows:
            table_name = table_row["name"]
            column_rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            schema[table_name] = [
                {
                    "name": column["name"],
                    "type": column["type"],
                    "not_null": bool(column["notnull"]),
                    "primary_key": bool(column["pk"]),
                }
                for column in column_rows
            ]

    return schema


def get_top_products_by_revenue(limit: int = 10) -> list[dict]:
    limit = _safe_limit(limit)
    query = """
        SELECT
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.line_revenue), 2) AS revenue,
            ROUND(SUM(oi.line_margin), 2) AS gross_margin,
            ROUND(SUM(oi.line_margin) / SUM(oi.line_revenue) * 100, 2) AS gross_margin_pct
        FROM order_items AS oi
        JOIN products AS p ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.sku, p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT ?
    """
    with _connect_read_only() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    return _rows_to_dicts(rows)


def get_monthly_sales_summary() -> list[dict]:
    query = """
        SELECT
            strftime('%Y-%m', o.order_date) AS month,
            COUNT(DISTINCT o.order_id) AS order_count,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.line_revenue), 2) AS revenue,
            ROUND(SUM(oi.line_cost), 2) AS cost,
            ROUND(SUM(oi.line_margin), 2) AS gross_margin,
            ROUND(SUM(oi.line_margin) / SUM(oi.line_revenue) * 100, 2) AS gross_margin_pct
        FROM orders AS o
        JOIN order_items AS oi ON oi.order_id = o.order_id
        GROUP BY strftime('%Y-%m', o.order_date)
        ORDER BY month
    """
    return run_read_only_query(query)


def get_low_stock_high_revenue_products(limit: int = 10) -> list[dict]:
    limit = _safe_limit(limit)
    query = """
        SELECT
            p.product_id,
            p.sku,
            p.product_name,
            p.category,
            i.stock_qty,
            i.reorder_level,
            SUM(oi.quantity) AS units_sold,
            ROUND(SUM(oi.line_revenue), 2) AS revenue,
            ROUND(SUM(oi.line_margin), 2) AS gross_margin
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
        ORDER BY revenue DESC
        LIMIT ?
    """
    with _connect_read_only() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    return _rows_to_dicts(rows)
