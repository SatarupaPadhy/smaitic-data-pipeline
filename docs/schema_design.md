# Warehouse Design Notes

## Tag Legend

- **[Confirmed]** Directly observed in the supplied sample data.
- **[Design]** A deliberate modeling choice.
- **[Assumption]** Accepted provisionally; not verified.
- **[Unverified]** Checked against the inspected sample but not established for the full dataset.

Each supplied JSON file contains a single inspected document. Counts such as 41 order items and 2 bill items describe these samples, not the production dataset.


## 1. Orders

- **Grain:** One row per order document.
- **Source identifier:** MongoDB `_id.$oid`.
- **Candidate measures:** `total_amt`, `savings_total`.
- **[Confirmed]** The source also contains `processing_duration`.
- **[Design]** Exclude `processing_duration` from the initial analytical model because neither schema diagram includes it. Reconsider it if processing-time analysis is required.
- **[Design]** `status` stays a plain attribute on the fact in both schemas, not a separate dimension.


## 2. Order Items

- **Grain:** One row per product entry within an order.
- **Parent identifier:** Source order ID from the parent order document.
- **Candidate measures:** `qty`, `price`, `unit_price`.
- **Candidate identifiers:** `product_id`, `supplier_product_id`, and supplier code.
- **[Confirmed]** The inspected order items contain no dedicated item-level ID.
- **[Design]** Generate `item_position` during ETL from the item's index in the source array. Combine it with the parent order ID to identify each row.
- **[Assumption]** Item positions are reproducible only while the source-array ordering remains stable.
- **[Design]** In the Star schema, `FACT_ORDER_ITEMS` stores `product_key` and `supplier_key`. In the Snowflake schema it stores `supplier_product_key`, which points to `BRIDGE_PRODUCT_SUPPLIER`.
- **[Confirmed]** In the inspected order, `qty × unit_price` equals `price` for all 41 items.


## 3. Bills

- **Grain:** One row per bill document.
- **Source identifier:** MongoDB `_id.$oid`.
- **Candidate measures:** `total`, `sub_total`, `taxes`, `shipping`, `paid_amount`.
- **Relationship:** One bill can contain multiple line items.
- **[Design]** Preserve the bill's supplier code as a plain attribute until a reliable mapping to the order supplier codes is established.
- **[Design]** `status` stays a plain attribute on the fact in both schemas.


## 4. Bill Items

- **Grain:** One row per line item within a bill.
- **Parent identifier:** Source bill ID from the parent bill document.
- **Candidate measures:** `qty`, `price`, `unit_price`.
- **[Confirmed]** The inspected bill line items contain no dedicated item-level ID, and no `product_id` or supplier field. They carry only `name`, `supplier_product_id`, `qty`, `price` and `unit_price`.
- **[Design]** Generate `item_position` during ETL from the item's index in the source array. Combine it with the parent bill ID to identify each row.
- **[Assumption]** Item positions are reproducible only while the source-array ordering remains stable.
- **[Design]** Do not link bill items to the product or supplier dimensions. They have no `product_id`, and the bill's supplier code was not observed among the order supplier codes (see 6.2). Keep `product_name` and `supplier_product_id` as plain attributes until a mapping is validated.


## 5. Initial Data Quality Observation

- **[Confirmed]** The inspected bill has `total = 50.16`, `sub_total = 38.66`, `shipping = 7.50`, and `taxes = 0`.
- **[Confirmed]** Subtotal plus shipping plus taxes equals `46.16`, leaving a discrepancy of `4.00`.
- **[Confirmed]** The bill line items sum to `sub_total`, and `discount_amount` is `0`.
- **[Confirmed]** No other amount or fee field that explains the discrepancy was observed in the inspected bill.
- **[Design]** Preserve the original source values and flag the discrepancy for investigation rather than silently modifying the data.
- **[Assumption]** The reason for the discrepancy is not established by the inspected record.


## 6. Candidate Dimensions

### 6.1 Date Dimension

- **[Confirmed]** Orders contain `created_at`; bills contain `inv_date` and `due_date`.
- **[Confirmed]** In the inspected files, order timestamps are stored as epoch milliseconds, while bill dates are stored as ISO 8601 strings.
- **[Design]** `FACT_ORDERS.date_key` is derived from `created_at`. `FACT_BILLS.invoice_date_key` is derived from `inv_date`. `due_date` remains a plain attribute on `FACT_BILLS`.
- **[Assumption]** Dates are derived in UTC. The ETL must apply one consistent time zone when converting timestamps to dates.
- **[Design]** The Star schema uses a flat `DIM_DATE` with day, month, month name, quarter, and year attributes.
- **[Design]** The Snowflake schema separates the hierarchy into date, month, quarter, and year tables.
- **[Design]** Month and quarter keys include the year so they stay unique across years. For example, October 2026 uses `month_key = 202610`, and Q4 2026 uses `quarter_key = 20264`.


### 6.2 Supplier Dimension

- **[Confirmed]** Each order item carries a supplier code (for example `HS`, `PATTERSON`). Bills carry a supplier code at the bill level.
- **[Design]** `DIM_SUPPLIER.supplier_code` stores the code. The order data contains no supplier names, so the model does not invent a name column.
- **[Design]** The Star schema stores `supplier_key` on `FACT_ORDER_ITEMS`. The Snowflake schema reaches the supplier through `BRIDGE_PRODUCT_SUPPLIER`.
- **[Unverified]** The inspected bill's supplier code `UC100111` does not appear among the inspected order supplier codes. This does not prove that no mapping exists in the full dataset.
- **[Design]** Keep `FACT_BILLS` unlinked to `DIM_SUPPLIER` until a valid cross-source mapping is established.


### 6.3 Product Dimension

- **[Design]** In the Star schema, one `DIM_PRODUCT` row represents one observed `(product_id, supplier_product_id)` combination. The supplier is carried separately by `supplier_key` on `FACT_ORDER_ITEMS`.
- **[Confirmed]** In the inspected order, the 41 items have 41 distinct `product_id` values and 41 distinct `supplier_product_id` values, with no duplicate pairs.
- **[Unverified]** This 1:1 relationship between `product_id` and `supplier_product_id` is established only for one order and may not hold across the full dataset.
- **[Assumption]** `product_name` is constant for a given `product_id`. The sample cannot test this because each product appears once.
- **[Design]** In the Snowflake schema, `BRIDGE_PRODUCT_SUPPLIER` represents supplier-specific offerings. Its proposed natural key is `(supplier_key, supplier_product_id)`, subject to uniqueness validation.
- **[Design]** Do not link `FACT_BILL_ITEMS` to `DIM_PRODUCT` until a reliable product mapping exists.


### 6.4 User / Clinic Dimension

- **[Confirmed]** Orders contain `user_id` and `group_id`. The inspected user document has its own `_id`.
- **[Unverified]** The inspected order's `user_id` does not match the inspected user's `_id`. One mismatch between two sample documents does not disprove a relationship, but it does not establish one.
- **[Design]** Keep `user_id` and `group_id` as plain columns in `FACT_ORDERS`. Do not introduce a linked user dimension until the relationship is validated.


## 7. Normalized Relational Migration (PostgreSQL)

This section describes the relational migration layer. It is separate from the Star and Snowflake analytical models.

- **[Design]** Create normalized tables for all three collections: `orders`, `order_items`, `bills`, `bill_items` and `users`. Each item table references its parent header table through the parent ID.
- **[Design]** Preserve the MongoDB source identifier on each header table for traceability.
- **[Confirmed]** The order-level `suppliers` list contains the same nine codes as the supplier values on the inspected items, so it is derivable from `order_items`.
- **[Design]** Do not store the `suppliers` list on `orders`, to avoid redundancy.
- **[Confirmed]** `users.json` contains scalar attributes such as `clinic_name`, `city`, `state`, `zip_code` and `group_id`, and multi-valued fields: `user_type`, `phone_no`, `phone_nos`, `roleId`, `departmentId` and `subgroup_ids`.
- **[Design]** Store the scalar user attributes in `users`. Move each multi-valued field into its own child table keyed by the user, so no column holds a list.
- **[Unverified]** `phone_no` and `phone_nos` both exist, and whether they overlap is not established. Keep them as separate sources until profiled.
- **[Design]** Exclude the password field from the migration. Treat email, name and phone values as personal data and review whether the analytical layer needs them.
- **[Design]** `orders.user_id` is stored as a plain column without an enforced foreign key, until the order-to-user relationship is validated (see 6.4).
- **[Design]** Defer `cart` and `priceMap` (see section 8).


## 8. Nested Fields and Exclusions

These fields are excluded from the initial analytical model. Raw ingestion or staging may still retain them for traceability.

| Source field | Decision and reason |
|---|---|
| `meta_data` | **[Confirmed]** The inspected order contains a per-supplier object (tax, total, `po_num`, `sub_total`, shipping), and the supplier totals sum to `total_amt`. **[Design]** Exclude from the initial model. Consider an order-by-supplier table if supplier-level reporting is needed. **[Assumption]** The totals match for other orders. |
| `is_backorder` | **[Confirmed]** Observed on 1 of the 41 inspected order items. **[Unverified]** Completeness across the full dataset is unknown. Excluded pending validation. |
| `lowest_price` | **[Design]** Exclude pending validation of its business meaning and structure. |
| `account_code_values` | **[Design]** Exclude pending profiling of its nested structure. |
| `image_url` | **[Design]** Exclude; product imagery is outside the analytical scope. |
| `processed_at` and other order timestamps | **[Design]** Exclude initially. Reconsider for processing latency analysis. |
| Order counts (`web_count`, `email_count`, and similar) | **[Design]** Exclude until their definitions are established. |
| `shipping_address` | **[Design]** Exclude initially. Reconsider if delivery geography is required. |
| `payment_methods` | **[Design]** Exclude pending profiling and reporting needs. |
| `supplier_order_ids` | **[Design]** Exclude until their link to supplier-level orders is validated. |
| Other bill header fields (`po_num`, `inv_num`, `bill_to`, `ship_to`, `approval_info`, `supplier_extra_info`) | **[Confirmed]** Present in the inspected bill. **[Design]** Exclude initially. `supplier_extra_info` contains a supplier name for the bill's supplier and could support a supplier name attribute later. |
| `cart` | **[Confirmed]** A nested field in the user document, with keys of the form `SUPPLIER:code`. **[Design]** Exclude; user/cart data is outside the current scope. |
| `priceMap` | **[Confirmed]** A supplier-keyed price structure in the inspected user document. **[Design]** Exclude until its structure and analytical purpose are validated. |


## 9. Modeling Assumptions and Validation

- **[Confirmed]** The inspected JSON documents are samples, not proof of full production volume or completeness.
- **[Design]** Preserve MongoDB source identifiers for traceability.
- **[Design]** Keep order-level and bill-level measures at their header grain. Do not sum them across item-level rows.
- **[Design]** `item_position` is ETL-generated from the array index and combined with the parent ID.
- **[Assumption]** This composite identifier is reproducible only while the source-array ordering remains stable.
- **[Unverified]** Relationships between orders, bills, users, products and suppliers require validation before foreign keys or analytical joins are relied upon.