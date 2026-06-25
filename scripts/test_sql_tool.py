from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.sql_tool import (  # noqa: E402
    get_database_schema,
    get_low_stock_high_revenue_products,
    get_monthly_sales_summary,
    get_top_products_by_revenue,
)


def print_schema() -> None:
    schema = get_database_schema()
    print("Database schema")
    print("---------------")
    for table_name, columns in schema.items():
        column_names = ", ".join(f"{column['name']} {column['type']}" for column in columns)
        print(f"{table_name}: {column_names}")
    print()


def print_rows(title: str, rows: list[dict], columns: list[str]) -> None:
    print(title)
    print("-" * len(title))
    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(str(row[column]) for column in columns))
    print()


def main() -> None:
    print_schema()
    print_rows(
        "Top 10 products by revenue",
        get_top_products_by_revenue(10),
        ["sku", "product_name", "category", "units_sold", "revenue", "gross_margin", "gross_margin_pct"],
    )
    print_rows(
        "Monthly sales summary",
        get_monthly_sales_summary(),
        ["month", "order_count", "units_sold", "revenue", "gross_margin", "gross_margin_pct"],
    )
    print_rows(
        "Low-stock high-revenue products",
        get_low_stock_high_revenue_products(10),
        ["sku", "product_name", "category", "stock_qty", "reorder_level", "units_sold", "revenue"],
    )


if __name__ == "__main__":
    main()
