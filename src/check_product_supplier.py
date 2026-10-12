
import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as file:
        data = json.load(file)

    # Handle either one document or a list of documents
    return data if isinstance(data, list) else [data]

orders = load_json("orders.json")
bills = load_json("bills.json")

product_suppliers = defaultdict(set)

# Collect supplier values for each product ID in orders
for order in orders:
    for item in order.get("products", []):
        product_id = item.get("product_id")
        supplier = item.get("supplier")

        if product_id and supplier:
            product_suppliers[product_id].add(supplier)

print("PRODUCTS ASSOCIATED WITH MULTIPLE SUPPLIERS")
for product_id, suppliers in product_suppliers.items():
    if len(suppliers) > 1:
        print(product_id, "->", sorted(suppliers))

print("\nORDER PRODUCT SAMPLE")
for order in orders[:2]:
    for item in order.get("products", [])[:5]:
        print({
            "product_id": item.get("product_id"),
            "supplier_product_id": item.get("supplier_product_id"),
            "supplier": item.get("supplier")
        })

print("\nBILL LINE ITEM SAMPLE")
for bill in bills[:2]:
    print("Bill supplier:", bill.get("supplier"))
    for item in bill.get("line_items", [])[:5]:
        print({
            "supplier_product_id": item.get("supplier_product_id"),
            "product_name": item.get("name")
        })

print("\nORDER SUPPLIER SUMMARY")
for order in orders:
    print("Order ID:", order.get("_id", {}).get("$oid"))
    print("Order suppliers:", order.get("suppliers"))
    print("Product supplier names:",
          sorted({
              item.get("supplier")
              for item in order.get("products", [])
              if item.get("supplier")
          }))

print("\nBILL SUPPLIER AND PRODUCT IDS")
for bill in bills:
    print("Bill supplier:", bill.get("supplier"))
    print("Line item supplier product IDs:",
          [
              item.get("supplier_product_id")
              for item in bill.get("line_items", [])
          ])
