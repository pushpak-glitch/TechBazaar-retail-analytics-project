"""TechBazaar retail sales: data validation, cleaning, EDA summary and year-on-year KPIs.

Input : dashboard/TechBazaar_KPI_PowerBI_ready.xlsx  (sheet "Sales_Data", 38,358 orders x 18 columns)
Output: data/sales_data.csv               raw export of the sheet, unchanged
        data/sales_cleaned.csv            snake_case, typed, with derived columns (Power BI / SQL ready)
        outputs/data_quality_checks.csv   every validation rule with its result
        outputs/billing_ratio_by_month.csv  how total_amount relates to quantity x unit_price, by month
        outputs/yoy_summary.csv           year-on-year KPIs

Run:  python src/eda_and_cleaning.py
"""
import numpy as np
import pandas as pd

from config import CLEAN, OUTPUTS, RAW, XLSX

OUTPUTS.mkdir(exist_ok=True)
RAW.parent.mkdir(exist_ok=True)
pd.set_option("display.width", 140)

# ------------------------------------------------------------------ 1. load
if RAW.exists():
    raw = pd.read_csv(RAW)
else:
    raw = pd.read_excel(XLSX, sheet_name="Sales_Data")
    raw.to_csv(RAW, index=False)
print(f"Loaded {len(raw):,} rows x {raw.shape[1]} columns")

df = raw.copy()
df.columns = (df.columns.str.strip().str.lower().str.replace(" ", "_"))
df = df.rename(columns={"profit_margin_pct": "margin_pct_on_total_amount"})  # what the column actually is (see checks)
df["date"] = pd.to_datetime(df["date"])
for c in ["order_id", "customer_id", "city", "category", "product_name", "payment_mode"]:
    df[c] = df[c].astype("string").str.strip()

df["net_sales"] = (df["quantity"] * df["unit_price"]).round(2)          # transaction value before the billing factor
df["billing_ratio"] = (df["total_amount"] / df["net_sales"]).round(4)   # total_amount / (qty x unit_price)
df["cost_total"] = (df["quantity"] * df["cost_price"]).round(2)

# ------------------------------------------------------------------ 2. validation rules
def check(rule, failing_rows, note=""):
    n = int(failing_rows)
    return {"rule": rule, "rows_failing": n, "pct_failing": round(n / len(df) * 100, 2), "note": note}

ratio = df["billing_ratio"]
checks = [
    check("no missing values", df.isna().any(axis=1).sum()),
    check("order_id unique", df["order_id"].duplicated().sum()),
    check("no fully duplicated rows", raw.duplicated().sum()),
    check("quantity >= 1", (df["quantity"] < 1).sum(), f"values seen: {sorted(int(q) for q in df['quantity'].unique())}"),
    check("unit_price = base_price x (1 - discount_pct/100)",
          (~np.isclose(df["unit_price"], df["base_price"] * (1 - df["discount_pct"] / 100), atol=0.01)).sum()),
    check("cost_price = 70% of base_price",
          (~np.isclose(df["cost_price"], df["base_price"] * 0.70, atol=0.01)).sum(),
          "every product costs exactly 70% of list price -> dataset is very likely synthetic"),
    check("profit = (unit_price - cost_price) x quantity",
          (~np.isclose(df["profit"], (df["unit_price"] - df["cost_price"]) * df["quantity"], atol=0.02)).sum()),
    check("total_amount = quantity x unit_price (within 1%)", ((ratio - 1).abs() > 0.01).sum(),
          f"ratio range {ratio.min():.3f}-{ratio.max():.3f}; follows a month-of-year pattern (see billing_ratio_by_month.csv)"),
    check("profit_margin_pct = profit / total_amount x 100",
          (~np.isclose(df["margin_pct_on_total_amount"], df["profit"] / df["total_amount"] * 100, atol=0.011)).sum(),
          "the supplied margin mixes two bases: profit is on qty x unit_price, the divisor is total_amount"),
    check("total_amount >= quantity x cost_price", (df["total_amount"] < df["cost_total"]).sum(),
          "rows billed below cost although recorded profit is positive"),
    check("year / month match date",
          ((df["year"] != df["date"].dt.year) | (df["month"] != df["date"].dt.month)).sum()),
    check("profit >= 0", (df["profit"] < 0).sum()),
]
dq = pd.DataFrame(checks)
dq.to_csv(OUTPUTS / "data_quality_checks.csv", index=False)
print("\nDATA-QUALITY CHECKS\n" + dq.to_string(index=False))

by_month = (df.groupby("month")["billing_ratio"]
            .agg(mean="mean", min="min", max="max").round(3))
by_month["orders_per_year"] = (df.groupby("month").size() / df["year"].nunique()).round(0).astype(int)
by_month.to_csv(OUTPUTS / "billing_ratio_by_month.csv")
print("\nBILLING RATIO (total_amount / qty x unit_price) BY MONTH\n" + by_month.to_string())

# ------------------------------------------------------------------ 3. cleaning decisions
# Nothing is dropped: no nulls, duplicates or impossible values. The issue is definitional, so we
#  * keep total_amount as recorded "billed revenue" (it is what the KPI workbook and Power BI use);
#  * add net_sales = qty x unit_price, the base `profit` is defined on;
#  * recompute margin on net_sales (consistent numerator and denominator) and keep the supplied
#    column under a name that says what it is;
#  * flag the rows billed below cost so they can be filtered in BI.
df["margin_pct"] = (df["profit"] / df["net_sales"] * 100).round(2)
df["billed_below_cost"] = df["total_amount"] < df["cost_total"]
df["month_name"] = df["date"].dt.strftime("%b")
df["quarter"] = "Q" + df["date"].dt.quarter.astype(str)
df["year_month"] = df["date"].dt.strftime("%Y-%m")
df["weekday"] = df["date"].dt.day_name()
df["is_festive_season"] = df["month"].isin([10, 11])  # Diwali / festive sale period
df["discount_band"] = df["discount_pct"].map(lambda d: "No discount" if d == 0 else f"{d}%")
df["date"] = df["date"].dt.strftime("%Y-%m-%d")

cols = ["order_id", "date", "year", "quarter", "month", "month_name", "year_month", "weekday", "is_festive_season",
        "customer_id", "city", "category", "product_name", "payment_mode", "quantity", "base_price", "discount_pct",
        "discount_band", "unit_price", "net_sales", "total_amount", "billing_ratio", "cost_price", "cost_total",
        "profit", "margin_pct", "margin_pct_on_total_amount", "billed_below_cost"]
df = df[cols]
df.to_csv(CLEAN, index=False)
print(f"\nSaved cleaned data -> {CLEAN.relative_to(CLEAN.parents[1])} ({len(df):,} rows, {len(cols)} columns)")

# ------------------------------------------------------------------ 4. quick EDA
print(f"\nDate range: {df['date'].min()} -> {df['date'].max()}")
print(f"Customers: {df['customer_id'].nunique():,} | Products: {df['product_name'].nunique()} | "
      f"Cities: {df['city'].nunique()} | Categories: {df['category'].nunique()}")
for col in ["city", "category", "payment_mode", "discount_band", "quantity"]:
    print(f"\n{col} (share of orders %)\n" + (df[col].value_counts(normalize=True) * 100).round(1).to_string())

yoy = df.groupby("year").agg(
    orders=("order_id", "count"),
    customers=("customer_id", "nunique"),
    billed_revenue=("total_amount", "sum"),
    net_sales=("net_sales", "sum"),
    profit=("profit", "sum"),
    avg_order_value=("total_amount", "mean"),
)
yoy["margin_pct_on_net_sales"] = yoy["profit"] / yoy["net_sales"] * 100
for c in ["orders", "billed_revenue", "net_sales", "profit", "avg_order_value"]:
    yoy[f"{c}_yoy_pct"] = yoy[c].pct_change() * 100
yoy = yoy.round(2)
yoy.to_csv(OUTPUTS / "yoy_summary.csv")
print("\nYEAR-ON-YEAR SUMMARY\n" + yoy.T.to_string(float_format=lambda v: f"{v:,.2f}"))
