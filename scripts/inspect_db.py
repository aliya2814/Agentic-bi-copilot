from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "processed" / "business.db"


def print_rows(title: str, columns: list[str], rows: list[sqlite3.Row]) -> None:
    print(title)
    print("-" * len(title))
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(str(row[column]) for column in columns))
    print()


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}. Run scripts/create_sample_db.py first.")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()
        table_names = [row["name"] for row in table_rows]

        print(f"Database: {DB_PATH}")
        print()
        print("Table names")
        print("-----------")
        for table_name in table_names:
            print(table_name)
        print()

        print("Row counts")
        print("----------")
        for table_name in table_names:
            count = conn.execute(f"SELECT COUNT(*) AS row_count FROM {table_name}").fetchone()["row_count"]
            print(f"{table_name}: {count}")
        print()

        product_rows = conn.execute(
            """
            SELECT product_id, sku, product_name, category, cost_price, sell_price, margin
            FROM products
            ORDER BY product_id
            LIMIT 5
            """
        ).fetchall()
        print_rows(
            "First 5 rows from products",
            ["product_id", "sku", "product_name", "category", "cost_price", "sell_price", "margin"],
            product_rows,
        )

        order_rows = conn.execute(
            """
            SELECT order_id, customer_id, order_date, channel, status, shipping_state, discount_pct
            FROM orders
            ORDER BY order_date, order_id
            LIMIT 5
            """
        ).fetchall()
        print_rows(
            "First 5 rows from orders",
            ["order_id", "customer_id", "order_date", "channel", "status", "shipping_state", "discount_pct"],
            order_rows,
        )

        top_products = conn.execute(
            """
            SELECT
                p.sku,
                p.product_name,
                p.category,
                SUM(oi.quantity) AS units_sold,
                ROUND(SUM(oi.line_revenue), 2) AS revenue,
                ROUND(SUM(oi.line_margin), 2) AS gross_margin
            FROM order_items AS oi
            JOIN products AS p ON p.product_id = oi.product_id
            GROUP BY p.product_id, p.sku, p.product_name, p.category
            ORDER BY revenue DESC
            LIMIT 10
            """
        ).fetchall()
        print_rows(
            "Top 10 products by revenue",
            ["sku", "product_name", "category", "units_sold", "revenue", "gross_margin"],
            top_products,
        )


if __name__ == "__main__":
    main()
