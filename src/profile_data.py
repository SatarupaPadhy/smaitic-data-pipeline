
# ============================================================
# SECTION 1: IMPORTS AND PROJECT PATHS
# ============================================================

import json
from pathlib import Path

# Find the project root and source data directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

# Source files to inspect
SOURCE_FILES = ["orders.json", "bills.json", "users.json"]


# ============================================================
# SECTION 2: BASIC JSON INSPECTION
# ============================================================

for filename in SOURCE_FILES:
    file_path = DATA_DIR / filename

    print(f"\n{'=' * 60}")
    print(f"FILE: {filename}")
    print("=" * 60)

    # Check whether the source file exists
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        continue

    # Load the JSON file once
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON: {error}")
        continue

    # Inspect the top-level structure
    print("Python data type:", type(data).__name__)

    if isinstance(data, list):
        print("Number of records:", len(data))
        if data:
            print("Top-level fields:", list(data[0].keys()))

    elif isinstance(data, dict):
        print("Top-level fields:", list(data.keys()))

    else:
        print("Unexpected top-level JSON structure.")
        continue


    # ========================================================
    # SECTION 3: NESTED DATA INSPECTION
    # ========================================================

    if filename == "orders.json":
        products = data.get("products", [])

        print("\nNested data: Products")
        print("Number of product entries:",
              len(products) if isinstance(products, list) else "Not a list")

        if isinstance(products, list) and products:
            print("Product entry fields:", list(products[0].keys()))

    elif filename == "bills.json":
        items = data.get("line_items", [])

        print("\nNested data: Bill line items")
        print("Number of line items:",
              len(items) if isinstance(items, list) else "Not a list")

        if isinstance(items, list) and items:
            print("Line-item fields:", list(items[0].keys()))

    elif filename == "users.json":
        cart = data.get("cart", {})
        price_map = data.get("priceMap")

        print("\nNested data: User")
        print("Cart type:", type(cart).__name__)
        print("Price map type:", type(price_map).__name__)

        if isinstance(cart, dict):
            print("Cart fields:", list(cart.keys()))

        if isinstance(price_map, dict):
            print("Number of suppliers in priceMap:", len(price_map))
