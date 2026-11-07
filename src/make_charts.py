"""Build the README charts from the SQL outputs (outputs/sql/*.csv) and the data-quality table.

Run:  python src/make_charts.py      (after src/load_and_query_sql.py)
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from config import IMAGES, OUTPUTS, SQL_OUT

IMAGES.mkdir(exist_ok=True)
BLUE, TEAL, GOLD, RED, PURPLE, GREY = "#3b6fb6", "#3fa999", "#d9a441", "#d1494a", "#8a6cc0", "#9aa3ad"
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "font.size": 10})
q = lambda name: pd.read_csv(SQL_OUT / f"{name}.csv")


def save(fig, name):
    fig.tight_layout()
    fig.savefig(IMAGES / name, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# 1. Monthly trend: billed revenue vs net sales vs orders --------------------------------------
m = q("q02_monthly_trend")
fig, ax = plt.subplots(figsize=(12, 4.8))
x = range(len(m))
ax2 = ax.twinx()
ax2.bar(x, m["orders"], color=GREY, alpha=0.25, width=0.7, label="Orders (right axis)")
ax2.set_ylim(0, m["orders"].max() * 2.2)
ax2.set_ylabel("Orders")
ax2.spines["top"].set_visible(False)
ax.plot(x, m["billed_revenue_lakh"] / 100, marker="o", color=BLUE, lw=2.2, label="Billed revenue (total_amount)")
ax.plot(x, m["net_sales_lakh"] / 100, marker="s", color=TEAL, lw=2, ls="--", label="Net sales (qty × unit price)")
ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
ax.set_xticks(list(x)); ax.set_xticklabels(m["year_month"], rotation=60, fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"₹{v:.1f}Cr"))
ax.set_ylabel("₹ crore per month")
ax.set_title("Monthly sales, Jan 2022 – Dec 2023: the Oct–Nov peak shows up in billed revenue, not in orders")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
ax.grid(axis="y", alpha=0.3)
save(fig, "01_monthly_trend.png")

# 2. Data quality: billing ratio by month ------------------------------------------------------
b = pd.read_csv(OUTPUTS / "billing_ratio_by_month.csv")
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.fill_between(range(12), b["min"], b["max"], color=BLUE, alpha=0.15, label="min–max across orders")
ax.plot(range(12), b["mean"], marker="o", color=BLUE, lw=2.2, label="average")
ax.axhline(1, color=RED, ls="--", lw=1.2, label="expected (= 1.0)")
for i, v in enumerate(b["mean"]):
    ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=8.5)
ax.set_xticks(range(12)); ax.set_xticklabels(months)
ax.set_ylabel("total_amount ÷ (quantity × unit_price)")
ax.set_title("Data check: billed amount is scaled by a month-of-year factor (0.78–1.65)")
ax.legend(frameon=False, loc="upper left")
save(fig, "02_data_check_billing_ratio.png")

# 3. City performance ---------------------------------------------------------------------------
c = q("q06_city_performance").sort_values("billed_revenue_cr")
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.4, 1]})
bars = axes[0].barh(c["city"], c["billed_revenue_cr"], color=BLUE)
for bar, v, s in zip(bars, c["billed_revenue_cr"], c["revenue_share_pct"]):
    axes[0].text(v + 0.5, bar.get_y() + bar.get_height() / 2, f"₹{v:.1f} Cr ({s:.0f}%)", va="center", fontsize=9)
axes[0].set_xlim(0, c["billed_revenue_cr"].max() * 1.3)
axes[0].set_xlabel("Billed revenue 2022–23 (₹ crore)")
axes[0].set_title("Revenue by city")
cols = [RED if v < 0 else TEAL for v in c["yoy_growth_pct"]]
axes[1].barh(c["city"], c["yoy_growth_pct"], color=cols)
for i, v in enumerate(c["yoy_growth_pct"]):
    axes[1].text(v + (0.2 if v >= 0 else -0.2), i, f"{v:+.1f}%", va="center", ha="left" if v >= 0 else "right", fontsize=9)
axes[1].axvline(0, color="black", lw=0.8)
axes[1].set_xlim(-4, 9)
axes[1].set_xlabel("2023 vs 2022 revenue growth (%)")
axes[1].set_title("Growth by city")
save(fig, "03_city_performance.png")

# 4. Category mix -------------------------------------------------------------------------------
k = q("q04_category_mix")
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
pal = [BLUE, TEAL, GOLD, PURPLE, RED]
axes[0].bar(k["category"], k["billed_revenue_cr"], color=pal)
for i, (v, s) in enumerate(zip(k["billed_revenue_cr"], k["revenue_share_pct"])):
    axes[0].text(i, v + 0.8, f"₹{v:.1f} Cr\n{s:.0f}%", ha="center", fontsize=9)
axes[0].set_ylim(0, k["billed_revenue_cr"].max() * 1.22)
axes[0].set_ylabel("₹ crore")
axes[0].set_title("Revenue by category (2022–23)")
axes[1].bar(k["category"], k["yoy_growth_pct"], color=pal)
for i, v in enumerate(k["yoy_growth_pct"]):
    axes[1].text(i, v + 0.2, f"+{v:.1f}%", ha="center", fontsize=9)
axes[1].set_ylabel("2023 vs 2022 growth (%)")
axes[1].set_title("Growth by category (margin is ~24.5% in every category)")
for a in axes:
    a.tick_params(axis="x", rotation=12)
save(fig, "04_category_mix.png")

# 5. Top products -------------------------------------------------------------------------------
p = q("q05_top_products").sort_values("billed_revenue_cr")
cat_col = {"Laptops": BLUE, "Televisions": TEAL, "Smartphones": GOLD, "Tablets": PURPLE, "Accessories": RED}
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(p["product_name"], p["billed_revenue_cr"], color=p["category"].map(cat_col))
for bar, v, s in zip(bars, p["billed_revenue_cr"], p["revenue_share_pct"]):
    ax.text(v + 0.2, bar.get_y() + bar.get_height() / 2, f"₹{v:.1f} Cr ({s:.1f}%)", va="center", fontsize=9)
ax.set_xlim(0, p["billed_revenue_cr"].max() * 1.25)
ax.set_xlabel("Billed revenue 2022–23 (₹ crore)")
ax.set_title("Top 10 products by revenue (of 25)")
handles = [plt.Rectangle((0, 0), 1, 1, color=cat_col[c]) for c in cat_col if c in set(p["category"])]
ax.legend(handles, [c for c in cat_col if c in set(p["category"])], frameon=False, loc="lower right")
save(fig, "05_top_products.png")

# 6. Discount vs margin -------------------------------------------------------------------------
d = q("q07_discount_vs_margin")
labels = ["None" if v == 0 else f"{v:.0f}%" for v in d["discount_pct"]]
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(labels, d["margin_pct"], color=[TEAL, "#6dbb9f", GOLD, "#e07b4f", RED])
for i, (v, o) in enumerate(zip(d["margin_pct"], d["order_share_pct"])):
    ax.text(i, v + 0.5, f"{v:.1f}% margin\n{o:.0f}% of orders", ha="center", fontsize=9)
ax.set_ylim(0, 37)
ax.set_xlabel("Discount given")
ax.set_ylabel("Profit margin on net sales (%)")
ax2 = ax.twinx()
ax2.plot(labels, d["avg_units_per_order"], color="black", marker="D", lw=1.5, label="Avg units per order (right)")
ax2.set_ylim(1.0, 1.8)
ax2.set_ylabel("Avg units per order")
ax2.spines["top"].set_visible(False)
ax2.legend(frameon=False, loc="upper right")
ax.set_title("Deeper discounts cut margin from 30% to 12.5% without bigger baskets")
save(fig, "06_discount_vs_margin.png")

# 7. RFM segments -------------------------------------------------------------------------------
r = q("q12_rfm_segments")
r["label"] = r["segment"].str[2:]
fig, ax = plt.subplots(figsize=(11, 4.5))
w = 0.38
xs = range(len(r))
ax.bar([i - w / 2 for i in xs], r["customer_share_pct"], w, color=GREY, label="Share of customers")
ax.bar([i + w / 2 for i in xs], r["revenue_share_pct"], w, color=BLUE, label="Share of revenue")
for i, (cs, rs, n) in enumerate(zip(r["customer_share_pct"], r["revenue_share_pct"], r["customers"])):
    ax.text(i - w / 2, cs + 0.6, f"{cs:.0f}%", ha="center", fontsize=8.5)
    ax.text(i + w / 2, rs + 0.6, f"{rs:.0f}%", ha="center", fontsize=8.5, color=BLUE, fontweight="bold")
ax.set_xticks(list(xs)); ax.set_xticklabels([f"{l}\n({n:,} cust.)" for l, n in zip(r["label"], r["customers"])])
ax.set_ylabel("%")
ax.set_ylim(0, r[["customer_share_pct", "revenue_share_pct"]].max().max() * 1.2)
ax.set_title("RFM customer segments (snapshot 1 Jan 2024): Champions are 22% of customers, 34% of revenue")
ax.legend(frameon=False)
save(fig, "07_rfm_segments.png")
