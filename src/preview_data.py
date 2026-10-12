
# ==================================================
# PREVIEW SOURCE DATA AS TABLES
# ==================================================

import json
import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
PREVIEW_DIR = PROJECT_DIR / "previews"

PREVIEW_DIR.mkdir(exist_ok=True)


def load_json(filename):
    """Load one JSON source document."""
    with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)



def write_csv(filename, rows):
    """Write dictionaries to CSV, including fields found in any row."""
    if not rows:
        print(f"No rows to write: {filename}")
        return

    # Collect all fields from every row, not just the first one
    fieldnames = list(dict.fromkeys(
        key for row in rows for key in row.keys()
    ))

    output_path = PREVIEW_DIR / filename

    with open(output_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="raise"
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created: previews/{filename} ({len(rows)} rows)")



# 1. Order-level preview: one row per order document
order = load_json("orders.json")
order_summary = {
    key: json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dict, list))
    else value
    for key, value in order.items()
    if key != "products"
}
write_csv("orders.csv", [order_summary])

# 2. Order-item preview: one row per product entry
order_items = order.get("products", [])
write_csv("order_items.csv", order_items)

# 3. Bill-level preview: one row per bill document
bill = load_json("bills.json")
bill_summary = {
    key: json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dict, list))
    else value
    for key, value in bill.items()
    if key != "line_items"
}
write_csv("bills.csv", [bill_summary])

# 4. Bill-item preview: one row per line item
bill_items = bill.get("line_items", [])
write_csv("bill_items.csv", bill_items)

# 5. User-level preview: one row per user document
user = load_json("users.json")
user_summary = {
    key: json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dict, list))
    else value
    for key, value in user.items()
}
write_csv("users.csv", [user_summary])
