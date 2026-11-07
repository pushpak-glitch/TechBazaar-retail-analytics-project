"""Run the whole pipeline: validation + cleaning -> SQLite + SQL queries -> charts."""
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
for step in ["eda_and_cleaning.py", "load_and_query_sql.py", "make_charts.py"]:
    print(f"\n{'=' * 70}\n>>> {step}\n{'=' * 70}")
    runpy.run_path(str(HERE / step), run_name="__main__")
