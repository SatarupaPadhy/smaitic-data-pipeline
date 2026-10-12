Deployed my 2+ years of hands-on ETL/ELT experience across Snowflake, Informatica IICS, Azure Data Factory, and Databricks/PySpark to build reliable, well-modeled data pipelines as a Data Engineer. I bring a solid foundation in dimensional modeling, SQL, and Python, and I want to grow by designing scalable pipelines that turn raw operational data into trusted, analytics-ready datasets.

# MongoDB to PostgreSQL Data Pipeline Design

Design for migrating three MongoDB collections (Orders, Bills, Users) into a normalized PostgreSQL schema, with Star and Snowflake analytical models.

## Scope

- **Included:** source data profiling scripts, a pipeline architecture diagram, a normalized relational design, Star and Snowflake schemas, and a document of assumptions.
- **Not included:** a production ETL implementation. The pipeline is a design; the scripts in `src/` profile and preview the supplied sample data.
- **Sample data:** each supplied JSON file contains one document, so all findings describe the samples and not the full dataset.

## Repository structure

```
data/        sample source documents (orders.json, bills.json, users.json)
docs/        architecture.mmd, star-schema.mmd, snowflake-schema.mmd, schema_design.md
previews/    CSV previews generated from the sample data
src/         profile_data.py, preview_data.py, check_product_supplier.py
```

## How to run

Requires Python 3. The scripts use only the standard library.

```
python src/profile_data.py
python src/preview_data.py
python src/check_product_supplier.py
```

- `profile_data.py` prints the structure of each source file.
- `preview_data.py` writes one CSV per table into `previews/`.
- `check_product_supplier.py` checks whether a product ID is associated with more than one supplier in the sample.

## Architecture

```mermaid
flowchart LR
    subgraph SRC["Source: MongoDB"]
        O["Orders collection"]
        B["Bills collection"]
        U["Users collection"]
    end

    subgraph EXT["Extract"]
        E["Read documents<br/>JSON export"]
    end

    subgraph STG["Staging: PostgreSQL"]
        S["Raw copy of each document<br/>kept for traceability"]
    end

    subgraph TRF["Transform"]
        T1["Flatten nested arrays<br/>products, line_items, user arrays"]
        T2["Generate item_position<br/>from array index"]
        T3["Derive date keys<br/>epoch ms and ISO strings to dates"]
        T4["Exclude password<br/>flag bill total discrepancy"]
    end

    subgraph REL["Load: normalized relational model"]
        R1["orders, order_items"]
        R2["bills, bill_items"]
        R3["users and child tables"]
    end

    subgraph DWH["Analytical models"]
        ST["Star schema"]
        SF["Snowflake schema"]
    end

    O --> E
    B --> E
    U --> E
    E --> S
    S --> T1
    T1 --> T2
    T2 --> T3
    T3 --> T4
    T4 --> R1
    T4 --> R2
    T4 --> R3
    R1 --> ST
    R2 --> ST
    R1 --> SF
    R2 --> SF
```

## Star schema

```mermaid
erDiagram
    FACT_ORDERS {
        string order_id PK
        string user_id
        string group_id
        string status
        decimal total_amt
        decimal savings_total
        datetime created_at
        date date_key FK
    }

    FACT_ORDER_ITEMS {
        string order_id PK, FK
        int item_position PK
        string product_key FK
        string supplier_key FK
        int qty
        decimal price
        decimal unit_price
    }

    FACT_BILLS {
        string bill_id PK
        string status
        string supplier
        decimal total
        decimal sub_total
        decimal taxes
        decimal shipping
        decimal paid_amount
        date invoice_date_key FK
        date due_date
    }

    FACT_BILL_ITEMS {
        string bill_id PK, FK
        int item_position PK
        string product_name
        string supplier_product_id
        int qty
        decimal price
        decimal unit_price
    }

    DIM_DATE {
        date date_key PK
        int day
        int month
        string month_name
        int quarter
        int year
    }

    DIM_PRODUCT {
        string product_key PK
        string product_id
        string supplier_product_id
        string product_name
    }

    DIM_SUPPLIER {
        string supplier_key PK
        string supplier_code
    }

    FACT_ORDERS ||--o{ FACT_ORDER_ITEMS : contains
    FACT_BILLS ||--o{ FACT_BILL_ITEMS : contains

    FACT_ORDERS }o--|| DIM_DATE : created_on
    FACT_BILLS }o--|| DIM_DATE : invoiced_on

    FACT_ORDER_ITEMS }o--|| DIM_PRODUCT : describes_product
    FACT_ORDER_ITEMS }o--|| DIM_SUPPLIER : supplied_by
```

## Snowflake schema

```mermaid
erDiagram
    FACT_ORDERS {
        string order_id PK
        string user_id
        string group_id
        string status
        decimal total_amt
        decimal savings_total
        date date_key FK
        datetime created_at
    }

    FACT_ORDER_ITEMS {
        string order_id PK, FK
        int item_position PK
        string supplier_product_key FK
        int qty
        decimal price
        decimal unit_price
    }

    FACT_BILLS {
        string bill_id PK
        string status
        string supplier
        decimal total
        decimal sub_total
        decimal taxes
        decimal shipping
        decimal paid_amount
        date invoice_date_key FK
        date due_date
    }

    FACT_BILL_ITEMS {
        string bill_id PK, FK
        int item_position PK
        string product_name
        string supplier_product_id
        int qty
        decimal price
        decimal unit_price
    }

    DIM_DATE {
        date date_key PK
        int day
        int month_key FK
    }

    DIM_MONTH {
        int month_key PK
        string month_name
        int quarter_key FK
    }

    DIM_QUARTER {
        int quarter_key PK
        int quarter
        int year_key FK
    }

    DIM_YEAR {
        int year_key PK
        int year
    }

    DIM_PRODUCT {
        string product_key PK
        string product_id
        string product_name
    }

    DIM_SUPPLIER {
        string supplier_key PK
        string supplier_code
    }

    BRIDGE_PRODUCT_SUPPLIER {
        string supplier_product_key PK
        string product_key FK
        string supplier_key FK
        string supplier_product_id
    }

    FACT_ORDERS ||--o{ FACT_ORDER_ITEMS : contains
    FACT_BILLS ||--o{ FACT_BILL_ITEMS : contains

    FACT_ORDERS }o--|| DIM_DATE : created_on
    FACT_BILLS }o--|| DIM_DATE : invoiced_on

    FACT_ORDER_ITEMS }o--|| BRIDGE_PRODUCT_SUPPLIER : references_offering
    BRIDGE_PRODUCT_SUPPLIER }o--|| DIM_PRODUCT : identifies_product
    BRIDGE_PRODUCT_SUPPLIER }o--|| DIM_SUPPLIER : identifies_supplier

    DIM_DATE }o--|| DIM_MONTH : belongs_to
    DIM_MONTH }o--|| DIM_QUARTER : belongs_to
    DIM_QUARTER }o--|| DIM_YEAR : belongs_to
```

## Design rationale

- **Star schema:** fewer joins and a flat date dimension, which suits straightforward reporting.
- **Snowflake schema:** removes repeated attributes by splitting the date hierarchy and separating supplier-specific product offerings into their own table, at the cost of extra joins.
- **Shared decisions:** order and bill measures stay at their header grain, and `item_position` is generated in the ETL because the source items have no item-level ID.

## Key assumptions

- Order `user_id` is kept as a plain column because the link to the Users collection could not be verified from the samples.
- Bill items are not linked to products or suppliers, because they carry no product ID and the sample bill's supplier code does not appear among the order supplier codes.
- The sample bill's total differs from its components by 4.00. The source values are preserved and the difference is flagged.
- The password field is excluded from the migration.

The full list of decisions, with each statement tagged as Confirmed, Design, Assumption or Unverified, is in [docs/schema_design.md](docs/schema_design.md). The diagram sources are in `docs/`.


