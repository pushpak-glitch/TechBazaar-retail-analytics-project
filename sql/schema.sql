-- TechBazaar retail sales: SQLite schema for the cleaned data (data/sales_cleaned.csv)
-- Works in MySQL / PostgreSQL with minor type changes (TEXT dates -> DATE, INTEGER flags -> BOOLEAN).

DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
    order_id                    TEXT PRIMARY KEY,
    date                        TEXT    NOT NULL,   -- ISO yyyy-mm-dd
    year                        INTEGER NOT NULL,
    quarter                     TEXT,
    month                       INTEGER NOT NULL,
    month_name                  TEXT,
    year_month                  TEXT,               -- yyyy-mm
    weekday                     TEXT,
    is_festive_season           INTEGER,            -- 1 = Oct-Nov
    customer_id                 TEXT    NOT NULL,
    city                        TEXT,
    category                    TEXT,
    product_name                TEXT,
    payment_mode                TEXT,
    quantity                    INTEGER CHECK (quantity > 0),
    base_price                  REAL,               -- list price per unit
    discount_pct                REAL,
    discount_band               TEXT,
    unit_price                  REAL,               -- base_price x (1 - discount_pct/100)
    net_sales                   REAL,               -- quantity x unit_price (base of profit)
    total_amount                REAL,               -- billed amount as recorded (see README data notes)
    billing_ratio               REAL,               -- total_amount / net_sales
    cost_price                  REAL,               -- per unit
    cost_total                  REAL,               -- quantity x cost_price
    profit                      REAL,               -- (unit_price - cost_price) x quantity
    margin_pct                  REAL,               -- profit / net_sales x 100
    margin_pct_on_total_amount  REAL,               -- original "Profit Margin Pct" column (mixed bases)
    billed_below_cost           INTEGER             -- 1 = total_amount < cost_total
);

CREATE INDEX idx_sales_date     ON sales(date);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_city     ON sales(city);
CREATE INDEX idx_sales_category ON sales(category);
