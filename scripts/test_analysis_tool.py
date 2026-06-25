from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.analysis_tool import (  # noqa: E402
    analyse_category_performance,
    analyse_inventory_risk,
    analyse_margin_pressure,
    analyse_monthly_sales_performance,
    generate_business_recommendations,
)


def print_money(value: float) -> str:
    return f"${value:,.2f}"


def print_monthly_sales_performance() -> None:
    result = analyse_monthly_sales_performance()
    print("Monthly sales performance")
    print("-------------------------")
    print(f"Latest month: {result['latest_month']} revenue {print_money(result['latest_month_revenue'])}")
    print(f"Previous month: {result['previous_month']} revenue {print_money(result['previous_month_revenue'])}")
    print(
        "MoM revenue change: "
        f"{print_money(result['revenue_change_amount'])} ({result['revenue_change_pct']}%)"
    )
    print(f"Latest orders: {result['latest_month_order_count']}")
    print(f"Previous orders: {result['previous_month_order_count']}")
    print(f"Latest gross margin: {print_money(result['latest_month_gross_margin'])}")
    print(f"Previous gross margin: {print_money(result['previous_month_gross_margin'])}")
    print()


def print_category_performance() -> None:
    result = analyse_category_performance()
    print("Category performance")
    print("--------------------")
    print(f"Latest month: {result['latest_month']}")
    print("Top growing categories:")
    for row in result["top_growing_categories"]:
        print(f"- {row['category']}: {print_money(row['change_amount'])} ({row['change_pct']}%)")
    print("Top declining categories:")
    if result["top_declining_categories"]:
        for row in result["top_declining_categories"]:
            print(f"- {row['category']}: {print_money(row['change_amount'])} ({row['change_pct']}%)")
    else:
        print("- No categories declined month over month.")
    print()


def print_margin_pressure() -> None:
    result = analyse_margin_pressure()
    print("Margin pressure")
    print("---------------")
    print(f"Products with supplier price increases: {result['price_increase_count']}")
    print("Categories most affected:")
    for row in result["categories_most_affected"][:3]:
        print(
            f"- {row['category']}: {row['products_affected']} products, "
            f"estimated impact {print_money(row['estimated_margin_impact'])}"
        )
    print("Top products with margin pressure:")
    for row in result["top_products_with_margin_pressure"][:5]:
        print(
            f"- {row['product_name']}: margin pct change {row['gross_margin_pct_change']} pts, "
            f"impact {print_money(row['estimated_margin_impact'])}"
        )
    print()


def print_inventory_risk() -> None:
    result = analyse_inventory_risk()
    print("Inventory risk")
    print("--------------")
    print(f"High-revenue low-stock products: {result['high_revenue_low_stock_count']}")
    print(f"Total estimated revenue at risk: {print_money(result['total_revenue_at_risk'])}")
    for row in result["top_inventory_risk_products"][:5]:
        print(
            f"- {row['product_name']}: stock {row['stock_qty']} vs reorder {row['reorder_level']}, "
            f"risk {print_money(row['estimated_revenue_at_risk'])} ({row['risk_level']})"
        )
    print()


def print_business_recommendations() -> None:
    result = generate_business_recommendations()
    print("Business recommendations")
    print("------------------------")
    print(result["executive_summary"])
    print("Key findings:")
    for finding in result["key_findings"]:
        print(f"- {finding}")
    print("Recommended actions:")
    for action in result["recommended_actions"]:
        print(f"- {action}")
    print(f"Evidence total revenue at risk: {print_money(result['evidence']['total_revenue_at_risk'])}")
    print()


def main() -> None:
    print_monthly_sales_performance()
    print_category_performance()
    print_margin_pressure()
    print_inventory_risk()
    print_business_recommendations()


if __name__ == "__main__":
    main()
