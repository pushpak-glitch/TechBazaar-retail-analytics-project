"""Load the cleaned sales data into SQLite and run every business query.

Creates data/techbazaar.db from sql/schema.sql + data/sales_cleaned.csv, then runs each
"-- name: <q>" block in sql/business_queries.sql and saves the result to outputs/sql/<q>.csv.

Run:  python src/load_and_query_sql.py      (after src/eda_and_cleaning.py)
"""
import re
import sqlite3

import pandas as pd

from config import CLEAN, DB, ROOT, SQL_FILE, SQL_OUT

if not CLEAN.exists():
    raise SystemExit("Run `python src/eda_and_cleaning.py` first to create data/sales_cleaned.csv.")
SQL_OUT.mkdir(parents=True, exist_ok=True)
pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)

df = pd.read_csv(CLEAN)
for flag in ["is_festive_season", "billed_below_cost"]:
    df[flag] = df[flag].astype(int)

with sqlite3.connect(DB) as con:
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    df.to_sql("sales", con, if_exists="append", index=False)
    n = con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    print(f"Loaded {n:,} rows into {DB.name} (SQLite {sqlite3.sqlite_version})")

    blocks = re.findall(r"-- name:\s*(\w+)\s*\n(.*?)(?=\n-- name:|\Z)", SQL_FILE.read_text(), re.S)
    for name, query in blocks:
        res = pd.read_sql_query(query, con)
        res.to_csv(SQL_OUT / f"{name}.csv", index=False)
        title = next((l.strip("- ").strip() for l in query.splitlines() if l.startswith("-- Q")), "")
        print(f"\n### {name}  {title}\n{res.to_string(index=False)}")
print(f"\n{len(blocks)} queries -> {SQL_OUT.relative_to(ROOT)}/")
