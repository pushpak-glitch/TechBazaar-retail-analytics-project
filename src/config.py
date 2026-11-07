"""Project paths, resolved from the repository root so scripts run from anywhere."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "dashboard" / "TechBazaar_KPI_PowerBI_ready.xlsx"   # source workbook (Sales_Data + Summary)
RAW = ROOT / "data" / "sales_data.csv"                             # raw export of Sales_Data
CLEAN = ROOT / "data" / "sales_cleaned.csv"                        # cleaned, analysis-ready (Power BI friendly)
DB = ROOT / "data" / "techbazaar.db"                               # SQLite db (generated, git-ignored)
SQL_FILE = ROOT / "sql" / "business_queries.sql"
IMAGES = ROOT / "images"
OUTPUTS = ROOT / "outputs"
SQL_OUT = OUTPUTS / "sql"
