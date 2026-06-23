import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings

warnings.filterwarnings("ignore")



# load csv file

df = pd.read_csv("../data/sales_data.csv", parse_dates=["date"])


print(f"Total rows       : {len(df):,}")
print(f"Null values      :\n{df.isnull().sum()}")
print(f"Duplicate orders : {df['order_id'].duplicated().sum()}")
print(f"Date range       : {df['date'].min().date()} → {df['date'].max().date()}")


# date modifying

df["year"]       = df["date"].dt.year
df["month"]      = df["date"].dt.month
df["month_name"] = df["date"].dt.strftime("%b")

# Profit in percentage

df["profit_margin_pct"] = (df["profit"] / df["total_amount"] * 100).round(2)

# save csv file

df.to_csv("../data/sales_cleaned.csv", index=False)

# total revenue per month and each year

monthly = (
    df.groupby(["year", "month"])["total_amount"]
    .sum()
    .reset_index()
)

fig, x = plt.subplots(figsize=(14, 5))

# year-wise plotting

for year, group in monthly.groupby("year"):
    x.plot(
        group["month"],
        group["total_amount"] / 100000,  # Convert to Lakhs
        marker="o",
        label=str(year),
        linewidth=2
    )

x.set_xticks(range(1, 13))
x.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

# rs in lakhs on y-axis

x.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x:.0f}L"))

x.set_title("Monthly Revenue Trend — 2022 vs 2023", fontweight="bold")
x.legend()
x.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("../analysis_output/01_monthly_revenue.png", dpi=150)
plt.close()



# revenue by city in ascending order

city_revenue = (
    df.groupby("city")["total_amount"]
    .sum()
    .sort_values(ascending=True)
)

fig, x = plt.subplots(figsize=(8, 4))
bars = x.barh(city_revenue.index, city_revenue.values / 10000000, color="#5b8fd9")


x.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x:.1f}Cr"))
x.set_title("Total Revenue by City (2022-2023)", fontweight="bold")


for bar, value in zip(bars, city_revenue.values):
    x.text(
        value / 10000000 + 0.3,
        bar.get_y() + bar.get_height() / 2,
        f"₹{value / 10000000:.1f}Cr",
        va="center",
        fontsize=9
    )

plt.tight_layout()
plt.savefig("../analysis_output/02_revenue_by_city.png", dpi=150)
plt.close()

# Har product category ka total revenue nikalo
category_revenue = (
    df.groupby("category")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 4))

bar_colors = ["#3fa999", "#d9a441", "#d1494a", "#5b8fd9", "#a07cc5"]
ax.bar(category_revenue.index, category_revenue.values / 1e7, color=bar_colors)

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₹{x:.0f}Cr"))
ax.set_title("Revenue by Product Category", fontweight="bold")

plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("../analysis_output/03_revenue_by_category.png", dpi=150)
plt.close()


# total order in each payment mode

payment_counts = (
    df.groupby("payment_mode")["order_id"]
    .count()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(figsize=(6, 5))
ax.pie(
    payment_counts.values,
    labels=payment_counts.index,
    autopct="%1.1f%%",
    colors=["#5b8fd9", "#3fa999", "#d9a441", "#d1494a", "#a07cc5"]
)
ax.set_title("Payment Mode Distribution", fontweight="bold")

plt.tight_layout()
plt.savefig("../analysis_output/04_payment_modes.png", dpi=150)
plt.close()

# avarage profit margin by category

avg_margin = (
    df.groupby("category")["profit_margin_pct"]
    .mean()
    .sort_values(ascending=False)
)

fig, a = plt.subplots(figsize=(8, 4))
a.bar(avg_margin.index, avg_margin.values, color="#4f9d6e")

a.set_ylabel("Avg Profit Margin (%)")
a.set_title("Average Profit Margin by Category", fontweight="bold")


for i, (category, value) in enumerate(avg_margin.items()):
    ax.text(i, value + 0.2, f"{value:.1f}%", ha="center", fontsize=10)

plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("../analysis_output/05_profit_margin.png", dpi=150)
plt.close()

#compare revenue across years

yoy_summary = df.groupby("year").agg(
    total_revenue   = ("total_amount", "sum"),
    total_profit    = ("profit", "sum"),
    total_orders    = ("order_id", "count"),
    avg_order_value = ("total_amount", "mean")
).round(2)

# Revenue growth in percentage

yoy_summary["revenue_growth_pct"] = yoy_summary["total_revenue"].pct_change() * 100

print("\n" + "=" * 55)
print("YEAR-ON-YEAR SUMMARY")
print("=" * 55)
print(yoy_summary.to_string())

# save CSV

yoy_summary.to_csv("../analysis_output/yoy_summary.csv")

print("\nSaari charts analysis_output/ mein save ho gayi hain.")
print("Cleaned data data/sales_cleaned.csv mein save ho gaya hai.")