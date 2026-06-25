from __future__ import annotations

import calendar
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


RANDOM_SEED = 42
ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "processed" / "business.db"


CATEGORIES = {
    "Car Audio": [
        "Component Speaker Set",
        "Compact Subwoofer",
        "Four Channel Amplifier",
        "DSP Tuning Processor",
        "Touchscreen Head Unit",
        "Premium Wiring Kit",
        "Sound Deadening Pack",
        "Underseat Subwoofer",
        "6x9 Speaker Pair",
        "Bluetooth Receiver",
        "Monoblock Amplifier",
        "Tweeter Upgrade Kit",
        "Reverse Camera Kit",
        "Bass Control Remote",
        "Speaker Spacer Set",
        "Factory Integration Harness",
    ],
    "4WD Accessories": [
        "Recovery Tracks",
        "Roof Rack Platform",
        "Vehicle Awning",
        "Air Compressor",
        "Electric Winch",
        "Snorkel Kit",
        "Drawer System",
        "Dual Battery Tray",
        "Bull Bar Mount Kit",
        "Recovery Hitch",
        "Tyre Deflator Kit",
        "Underbody Protection Plate",
        "Tailgate Storage Bag",
        "Jerry Can Holder",
        "Sand Flag Kit",
        "Cargo Barrier",
    ],
    "Lighting": [
        "LED Light Bar",
        "Driving Light Pair",
        "Work Light Pair",
        "Rock Light Kit",
        "Headlight Upgrade Kit",
        "Fog Light Kit",
        "Camp Light Strip",
        "Beacon Light",
        "Wiring Harness",
        "Number Plate Light",
        "Interior Light Kit",
        "Trailer Light Kit",
        "Scene Light",
        "Reverse Light Kit",
        "Spotlight Cover Set",
        "Dimmer Switch Kit",
    ],
    "Touring": [
        "Fridge Slide",
        "Solar Blanket",
        "Portable Power Box",
        "Water Tank",
        "Roof Top Tent",
        "Camp Chair Set",
        "Folding Camp Table",
        "Shower Ensuite",
        "Portable Stove",
        "Canvas Storage Bag",
        "Battery Monitor",
        "12V Fan",
        "Travel Oven",
        "Recovery Shovel",
        "Privacy Screen",
        "Camp Kitchen Box",
    ],
    "Marine Audio": [
        "Marine Speaker Pair",
        "Marine Head Unit",
        "Marine Subwoofer",
        "Marine Amplifier",
        "Wake Tower Speaker Pair",
        "Waterproof Remote",
        "Marine Antenna",
        "Boat Wiring Kit",
        "Marine RGB Controller",
        "Deck Speaker Spacer",
        "NMEA Audio Interface",
        "Marine Fuse Block",
        "Waterproof RCA Cable",
        "Boat Sound Deadening",
        "Marine Bluetooth Receiver",
        "Pontoon Speaker Kit",
    ],
}


SUPPLIERS = [
    (1, "Southern Cross Audio", "Australia", 6, 0.96),
    (2, "Outback Gear Supply", "Australia", 8, 0.94),
    (3, "BrightTrack Lighting", "Australia", 5, 0.93),
    (4, "NorthStar Marine Systems", "New Zealand", 11, 0.91),
    (5, "TrailPro Touring Co", "Australia", 9, 0.92),
    (6, "Apex Auto Electronics", "China", 18, 0.88),
    (7, "Coastal Sound Imports", "United States", 21, 0.86),
    (8, "RidgeLine 4x4 Wholesale", "Thailand", 16, 0.89),
]


CATEGORY_SUPPLIERS = {
    "Car Audio": [1, 6, 7],
    "4WD Accessories": [2, 8, 5],
    "Lighting": [3, 6, 8],
    "Touring": [5, 2, 8],
    "Marine Audio": [4, 7, 1],
}


PRICE_RANGES = {
    "Car Audio": (35, 420, 1.55, 2.10),
    "4WD Accessories": (55, 950, 1.45, 1.95),
    "Lighting": (18, 360, 1.60, 2.25),
    "Touring": (22, 780, 1.50, 2.05),
    "Marine Audio": (30, 520, 1.55, 2.15),
}


CHANNELS = [
    ("Google Ads", 5200, 1.15),
    ("Meta Ads", 3400, 0.85),
    ("Email", 900, 1.40),
    ("SEO/Content", 1800, 0.75),
    ("Retail Events", 1600, 0.65),
    ("Marketplace", 2600, 0.95),
]


CHANNEL_CATEGORY_BOOSTS = {
    "Google Ads": {"Car Audio": 1.30, "Lighting": 1.18},
    "Meta Ads": {"Touring": 1.28, "4WD Accessories": 1.18},
    "Email": {"Car Audio": 1.20, "Touring": 1.15},
    "SEO/Content": {"Marine Audio": 1.16, "4WD Accessories": 1.12},
    "Retail Events": {"4WD Accessories": 1.35, "Touring": 1.25},
    "Marketplace": {"Lighting": 1.35, "Car Audio": 1.14},
}


STATES_AND_CITIES = {
    "NSW": ["Sydney", "Newcastle", "Wollongong", "Tamworth"],
    "VIC": ["Melbourne", "Geelong", "Ballarat", "Bendigo"],
    "QLD": ["Brisbane", "Gold Coast", "Townsville", "Cairns"],
    "WA": ["Perth", "Bunbury", "Geraldton", "Albany"],
    "SA": ["Adelaide", "Mount Gambier", "Port Lincoln"],
    "TAS": ["Hobart", "Launceston"],
    "ACT": ["Canberra"],
    "NT": ["Darwin", "Alice Springs"],
}


FIRST_NAMES = [
    "Alex",
    "Sam",
    "Jordan",
    "Taylor",
    "Casey",
    "Morgan",
    "Riley",
    "Jamie",
    "Chris",
    "Pat",
    "Avery",
    "Drew",
]


LAST_NAMES = [
    "Smith",
    "Nguyen",
    "Brown",
    "Wilson",
    "Taylor",
    "Singh",
    "Patel",
    "Martin",
    "Lee",
    "Walker",
    "King",
    "Young",
]


BUSINESS_WORDS = [
    "Auto",
    "Fleet",
    "Touring",
    "Electrical",
    "Marine",
    "Adventure",
    "Performance",
    "Installations",
]


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def month_starts(today: date) -> list[date]:
    first_of_month = date(today.year, today.month, 1)
    return [add_months(first_of_month, offset) for offset in range(-11, 1)]


def month_end(month_start: date, today: date) -> date:
    if month_start.year == today.year and month_start.month == today.month:
        return today
    last_day = calendar.monthrange(month_start.year, month_start.month)[1]
    return date(month_start.year, month_start.month, last_day)


def random_date_between(start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def round_price(value: float) -> float:
    dollars = int(value)
    return round(dollars + 0.99, 2)


def seasonality_for_category(category: str, month: int) -> float:
    if category == "Marine Audio":
        return {12: 1.65, 1: 1.55, 2: 1.35, 11: 1.20}.get(month, 0.82)
    if category == "4WD Accessories":
        return {4: 1.25, 5: 1.45, 6: 1.55, 7: 1.40, 9: 1.18}.get(month, 1.0)
    if category == "Lighting":
        return {5: 1.25, 6: 1.50, 7: 1.45, 8: 1.30}.get(month, 1.0)
    if category == "Touring":
        return {4: 1.20, 5: 1.30, 6: 1.35, 9: 1.20, 10: 1.25, 12: 1.18}.get(month, 1.0)
    if category == "Car Audio":
        return {11: 1.25, 12: 1.45, 1: 1.20, 6: 1.15}.get(month, 1.0)
    return 1.0


def marketing_seasonality(month: int) -> float:
    return {
        1: 1.10,
        4: 1.08,
        5: 1.12,
        6: 1.25,
        11: 1.28,
        12: 1.38,
    }.get(month, 1.0)


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            segment TEXT NOT NULL,
            state TEXT NOT NULL,
            city TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            supplier_name TEXT NOT NULL,
            country TEXT NOT NULL,
            lead_time_days INTEGER NOT NULL,
            reliability_score REAL NOT NULL
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            sku TEXT NOT NULL UNIQUE,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            supplier_id INTEGER NOT NULL,
            cost_price REAL NOT NULL,
            sell_price REAL NOT NULL,
            margin REAL NOT NULL,
            margin_pct REAL NOT NULL,
            demand_weight REAL NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            shipping_state TEXT NOT NULL,
            discount_pct REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        );

        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL,
            discount_pct REAL NOT NULL,
            line_revenue REAL NOT NULL,
            line_cost REAL NOT NULL,
            line_margin REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );

        CREATE TABLE inventory (
            product_id INTEGER PRIMARY KEY,
            stock_qty INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL,
            warehouse_location TEXT NOT NULL,
            last_stocktake_date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );

        CREATE TABLE supplier_price_changes (
            change_id INTEGER PRIMARY KEY,
            supplier_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            change_date TEXT NOT NULL,
            old_cost_price REAL NOT NULL,
            new_cost_price REAL NOT NULL,
            change_pct REAL NOT NULL,
            reason TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );

        CREATE TABLE returns (
            return_id INTEGER PRIMARY KEY,
            order_item_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            return_date TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT NOT NULL,
            refund_amount REAL NOT NULL,
            FOREIGN KEY (order_item_id) REFERENCES order_items (order_item_id),
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id),
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        );

        CREATE TABLE marketing_spend (
            spend_id INTEGER PRIMARY KEY,
            month TEXT NOT NULL,
            channel TEXT NOT NULL,
            spend_amount REAL NOT NULL,
            campaign_name TEXT NOT NULL
        );

        CREATE INDEX idx_orders_order_date ON orders (order_date);
        CREATE INDEX idx_orders_channel ON orders (channel);
        CREATE INDEX idx_order_items_product_id ON order_items (product_id);
        CREATE INDEX idx_products_category ON products (category);
        CREATE INDEX idx_marketing_spend_month ON marketing_spend (month);
        """
    )


def build_customers(months: list[date]) -> list[tuple]:
    customers = []
    start_date = add_months(months[0], -12)
    for customer_id in range(1, 201):
        segment = random.choices(
            ["Retail", "Trade", "Fleet", "Online"],
            weights=[0.45, 0.25, 0.08, 0.22],
            k=1,
        )[0]
        state = random.choices(
            list(STATES_AND_CITIES.keys()),
            weights=[0.31, 0.25, 0.21, 0.09, 0.06, 0.03, 0.03, 0.02],
            k=1,
        )[0]
        city = random.choice(STATES_AND_CITIES[state])

        if segment in {"Trade", "Fleet"}:
            customer_name = f"{city} {random.choice(BUSINESS_WORDS)} {random.choice(['Co', 'Group', 'Works', 'Supply'])}"
        else:
            customer_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        email_slug = customer_name.lower().replace(" ", ".").replace("'", "")
        email = f"{email_slug}{customer_id}@example.com"
        created_at = random_date_between(start_date, months[-1]).isoformat()
        customers.append((customer_id, customer_name, segment, state, city, email, created_at))
    return customers


def build_products(months: list[date]) -> tuple[list[dict], list[tuple]]:
    products = []
    price_changes = []
    product_id = 1
    change_id = 1
    high_demand_indexes = {0, 1, 4, 7}

    for category, product_names in CATEGORIES.items():
        min_cost, max_cost, min_markup, max_markup = PRICE_RANGES[category]
        for index, name in enumerate(product_names):
            supplier_id = random.choice(CATEGORY_SUPPLIERS[category])
            base_cost = round(random.uniform(min_cost, max_cost), 2)
            base_sell = round_price(base_cost * random.uniform(min_markup, max_markup))
            demand_weight = round(random.uniform(0.75, 1.25), 2)
            if index in high_demand_indexes:
                demand_weight = round(random.uniform(2.2, 4.4), 2)

            sku_prefix = "".join(word[0] for word in category.split())
            product = {
                "product_id": product_id,
                "sku": f"{sku_prefix}-{product_id:03d}",
                "product_name": f"{random.choice(['Apex', 'Summit', 'TrailMax', 'Coastal', 'Vector'])} {name}",
                "category": category,
                "supplier_id": supplier_id,
                "base_cost": base_cost,
                "base_sell": base_sell,
                "current_cost": base_cost,
                "current_sell": base_sell,
                "demand_weight": demand_weight,
                "price_change_date": None,
            }
            products.append(product)
            product_id += 1

    change_candidates = random.sample(products, 24)
    change_months = months[6:]
    for product in change_candidates:
        old_cost = product["base_cost"]
        change_pct = round(random.uniform(0.06, 0.18), 4)
        new_cost = round(old_cost * (1 + change_pct), 2)
        pass_through = random.uniform(0.0, 0.55)
        new_sell = round_price(product["base_sell"] + ((new_cost - old_cost) * pass_through))
        change_date = random_date_between(random.choice(change_months), months[-1])

        product["current_cost"] = new_cost
        product["current_sell"] = new_sell
        product["price_change_date"] = change_date

        price_changes.append(
            (
                change_id,
                product["supplier_id"],
                product["product_id"],
                change_date.isoformat(),
                old_cost,
                new_cost,
                round(change_pct * 100, 2),
                random.choice(["Factory price increase", "Freight surcharge", "FX movement", "Material cost increase"]),
            )
        )
        change_id += 1

    return products, price_changes


def product_prices_for_date(product: dict, order_date: date) -> tuple[float, float]:
    if product["price_change_date"] and order_date >= product["price_change_date"]:
        return product["current_cost"], product["current_sell"]
    return product["base_cost"], product["base_sell"]


def build_marketing_spend(months: list[date]) -> tuple[list[tuple], dict[str, dict[str, float]]]:
    spend_rows = []
    spend_by_month = {}
    spend_id = 1

    for month_start in months:
        month_key = month_start.strftime("%Y-%m")
        spend_by_month[month_key] = {}
        for channel, base_spend, _efficiency in CHANNELS:
            channel_factor = 1.0
            if channel == "Retail Events" and month_start.month in {4, 5, 6, 9}:
                channel_factor = 1.45
            elif channel == "Meta Ads" and month_start.month in {10, 11, 12}:
                channel_factor = 1.25
            elif channel == "Email" and month_start.month in {6, 11, 12}:
                channel_factor = 1.35

            spend = base_spend * marketing_seasonality(month_start.month) * channel_factor
            spend = round((spend * random.uniform(0.88, 1.14)) / 50) * 50
            campaign_name = f"{month_start.strftime('%b')} {channel} campaign"
            spend_rows.append((spend_id, month_key, channel, spend, campaign_name))
            spend_by_month[month_key][channel] = spend
            spend_id += 1

    return spend_rows, spend_by_month


def choose_category(order_date: date, channel: str) -> str:
    categories = list(CATEGORIES.keys())
    weights = []
    for category in categories:
        weight = seasonality_for_category(category, order_date.month)
        weight *= CHANNEL_CATEGORY_BOOSTS.get(channel, {}).get(category, 1.0)
        weights.append(weight)
    return random.choices(categories, weights=weights, k=1)[0]


def choose_product(category: str, products_by_category: dict[str, list[dict]]) -> dict:
    products = products_by_category[category]
    weights = [product["demand_weight"] for product in products]
    return random.choices(products, weights=weights, k=1)[0]


def build_orders(
    months: list[date],
    today: date,
    customers: list[tuple],
    products: list[dict],
    spend_by_month: dict[str, dict[str, float]],
) -> tuple[list[tuple], list[tuple], list[tuple], dict[int, int]]:
    orders = []
    order_items = []
    returns = []
    units_sold = {product["product_id"]: 0 for product in products}
    products_by_category = {
        category: [product for product in products if product["category"] == category]
        for category in CATEGORIES
    }

    customers_by_id = {customer[0]: customer for customer in customers}
    channel_efficiency = {channel: efficiency for channel, _base, efficiency in CHANNELS}
    return_rates = {
        "Car Audio": 0.034,
        "4WD Accessories": 0.022,
        "Lighting": 0.029,
        "Touring": 0.020,
        "Marine Audio": 0.026,
    }
    return_reasons = ["Wrong fitment", "Changed mind", "Damaged in transit", "Warranty issue", "Ordered duplicate"]

    order_id = 1
    order_item_id = 1
    return_id = 1

    for month_start in months:
        month_key = month_start.strftime("%Y-%m")
        spend_total = sum(spend_by_month[month_key].values())
        monthly_season = 1.0 + ((marketing_seasonality(month_start.month) - 1.0) * 0.55)
        order_count = int((108 * monthly_season) + (spend_total / 430) + random.randint(-8, 12))

        channels = [channel for channel, _base, _efficiency in CHANNELS]
        channel_weights = [
            18 + (spend_by_month[month_key][channel] / 100) * channel_efficiency[channel]
            for channel in channels
        ]

        for _ in range(order_count):
            order_date = random_date_between(month_start, month_end(month_start, today))
            channel = random.choices(channels, weights=channel_weights, k=1)[0]
            customer = random.choice(customers)
            customer_id = customer[0]
            segment = customer[2]
            shipping_state = customers_by_id[customer_id][3]
            status = random.choices(["Completed", "Shipped", "Processing"], weights=[0.90, 0.07, 0.03], k=1)[0]
            discount_pct = random.choices([0.0, 0.05, 0.10, 0.15], weights=[0.60, 0.24, 0.12, 0.04], k=1)[0]
            if channel in {"Email", "Retail Events"}:
                discount_pct = max(discount_pct, random.choice([0.05, 0.10]))

            orders.append((order_id, customer_id, order_date.isoformat(), channel, status, shipping_state, discount_pct))

            item_count = random.choices([2, 3, 4, 5], weights=[0.44, 0.34, 0.16, 0.06], k=1)[0]
            selected_product_ids = set()
            for _item_index in range(item_count):
                category = choose_category(order_date, channel)
                product = choose_product(category, products_by_category)
                attempts = 0
                while product["product_id"] in selected_product_ids and attempts < 5:
                    product = choose_product(category, products_by_category)
                    attempts += 1
                selected_product_ids.add(product["product_id"])

                unit_cost, unit_price = product_prices_for_date(product, order_date)
                quantity = random.choices([1, 2, 3, 4, 5, 6], weights=[0.47, 0.28, 0.12, 0.07, 0.04, 0.02], k=1)[0]
                if segment in {"Trade", "Fleet"}:
                    quantity += random.choice([0, 1, 2])
                if category in {"4WD Accessories", "Touring"}:
                    quantity = max(1, quantity - random.choice([0, 1]))

                line_revenue = round(unit_price * quantity * (1 - discount_pct), 2)
                line_cost = round(unit_cost * quantity, 2)
                line_margin = round(line_revenue - line_cost, 2)

                order_items.append(
                    (
                        order_item_id,
                        order_id,
                        product["product_id"],
                        quantity,
                        unit_price,
                        unit_cost,
                        discount_pct,
                        line_revenue,
                        line_cost,
                        line_margin,
                    )
                )
                units_sold[product["product_id"]] += quantity

                return_probability = return_rates[category]
                if channel == "Marketplace":
                    return_probability += 0.008
                if random.random() < return_probability:
                    return_qty = min(quantity, random.choices([1, 2], weights=[0.84, 0.16], k=1)[0])
                    return_date = order_date + timedelta(days=random.randint(5, 45))
                    if return_date <= today:
                        refund_amount = round(unit_price * return_qty * (1 - discount_pct), 2)
                        returns.append(
                            (
                                return_id,
                                order_item_id,
                                order_id,
                                product["product_id"],
                                customer_id,
                                return_date.isoformat(),
                                return_qty,
                                random.choice(return_reasons),
                                refund_amount,
                            )
                        )
                        return_id += 1

                order_item_id += 1

            order_id += 1

    return orders, order_items, returns, units_sold


def build_inventory(products: list[dict], units_sold: dict[int, int], today: date) -> list[tuple]:
    top_sellers = sorted(units_sold, key=units_sold.get, reverse=True)
    low_stock_high_sellers = set(top_sellers[:9])
    strong_sellers = set(top_sellers[:20])
    locations = ["Sydney DC", "Melbourne DC", "Brisbane DC", "Perth DC"]
    inventory = []

    for product in products:
        product_id = product["product_id"]
        if product_id in low_stock_high_sellers:
            stock_qty = random.randint(4, 18)
            reorder_level = random.randint(24, 52)
        elif product_id in strong_sellers:
            stock_qty = random.randint(19, 65)
            reorder_level = random.randint(22, 48)
        else:
            stock_qty = random.randint(32, 240)
            reorder_level = random.randint(12, 36)

        inventory.append(
            (
                product_id,
                stock_qty,
                reorder_level,
                random.choice(locations),
                (today - timedelta(days=random.randint(1, 21))).isoformat(),
            )
        )

    return inventory


def insert_data(
    conn: sqlite3.Connection,
    customers: list[tuple],
    products: list[dict],
    price_changes: list[tuple],
    marketing_spend: list[tuple],
    orders: list[tuple],
    order_items: list[tuple],
    returns: list[tuple],
    inventory: list[tuple],
) -> None:
    product_rows = []
    for product in products:
        margin = round(product["current_sell"] - product["current_cost"], 2)
        margin_pct = round((margin / product["current_sell"]) * 100, 2)
        product_rows.append(
            (
                product["product_id"],
                product["sku"],
                product["product_name"],
                product["category"],
                product["supplier_id"],
                product["current_cost"],
                product["current_sell"],
                margin,
                margin_pct,
                product["demand_weight"],
            )
        )

    conn.executemany(
        """
        INSERT INTO customers (
            customer_id, customer_name, segment, state, city, email, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        customers,
    )
    conn.executemany(
        """
        INSERT INTO suppliers (
            supplier_id, supplier_name, country, lead_time_days, reliability_score
        ) VALUES (?, ?, ?, ?, ?)
        """,
        SUPPLIERS,
    )
    conn.executemany(
        """
        INSERT INTO products (
            product_id, sku, product_name, category, supplier_id, cost_price,
            sell_price, margin, margin_pct, demand_weight
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        product_rows,
    )
    conn.executemany(
        """
        INSERT INTO orders (
            order_id, customer_id, order_date, channel, status, shipping_state, discount_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        orders,
    )
    conn.executemany(
        """
        INSERT INTO order_items (
            order_item_id, order_id, product_id, quantity, unit_price, unit_cost,
            discount_pct, line_revenue, line_cost, line_margin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        order_items,
    )
    conn.executemany(
        """
        INSERT INTO inventory (
            product_id, stock_qty, reorder_level, warehouse_location, last_stocktake_date
        ) VALUES (?, ?, ?, ?, ?)
        """,
        inventory,
    )
    conn.executemany(
        """
        INSERT INTO supplier_price_changes (
            change_id, supplier_id, product_id, change_date, old_cost_price,
            new_cost_price, change_pct, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        price_changes,
    )
    conn.executemany(
        """
        INSERT INTO returns (
            return_id, order_item_id, order_id, product_id, customer_id,
            return_date, quantity, reason, refund_amount
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        returns,
    )
    conn.executemany(
        """
        INSERT INTO marketing_spend (
            spend_id, month, channel, spend_amount, campaign_name
        ) VALUES (?, ?, ?, ?, ?)
        """,
        marketing_spend,
    )
    conn.commit()


def print_summary(conn: sqlite3.Connection, months: list[date], today: date) -> None:
    tables = [
        "customers",
        "suppliers",
        "products",
        "orders",
        "order_items",
        "inventory",
        "supplier_price_changes",
        "returns",
        "marketing_spend",
    ]

    print(f"Created sample database: {DB_PATH}")
    print(f"Order date range: {months[0].isoformat()} to {today.isoformat()}")
    print("Row counts:")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count}")


def main() -> None:
    random.seed(RANDOM_SEED)
    today = date.today()
    months = month_starts(today)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    customers = build_customers(months)
    products, price_changes = build_products(months)
    marketing_spend, spend_by_month = build_marketing_spend(months)
    orders, order_items, returns, units_sold = build_orders(months, today, customers, products, spend_by_month)
    inventory = build_inventory(products, units_sold, today)

    with sqlite3.connect(DB_PATH) as conn:
        create_schema(conn)
        insert_data(
            conn,
            customers,
            products,
            price_changes,
            marketing_spend,
            orders,
            order_items,
            returns,
            inventory,
        )
        print_summary(conn, months, today)


if __name__ == "__main__":
    main()
