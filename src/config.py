"""
Project-wide configuration and path management.
"""
import os
from pathlib import Path

# ─── Directory Layout ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"
SQL_DIR = BASE_DIR / "sql"

# ─── Database ─────────────────────────────────────────────────────────────────
DB_PATH = DATA_DIR / "credit_risk.db"

# ─── Kaggle Dataset ───────────────────────────────────────────────────────────
# After downloading from Kaggle, place the CSV here:
#   https://www.kaggle.com/datasets/wordsforthewise/lending-club
LENDING_CLUB_CSV = RAW_DATA_DIR / "loan.csv"

# ─── Synthetic Data Settings (used when real CSV is absent) ──────────────────
SYNTHETIC_RECORDS = 250_000
RANDOM_SEED = 42

# ─── Risk Thresholds (used for colour-coding in dashboard) ───────────────────
RISK_LOW_THRESHOLD = 0.10     # below 10% default rate  → green
RISK_HIGH_THRESHOLD = 0.20    # above 20% default rate  → red

# ─── Loan Status Classification ───────────────────────────────────────────────
DEFAULT_STATUSES = {
    "Charged Off",
    "Default",
    "Late (31-120 days)",
    "Does not meet the credit policy. Status:Charged Off",
}

# ─── Derived Field Bins ───────────────────────────────────────────────────────
LOAN_AMOUNT_BINS   = [0, 10_000, 20_000, 30_000, 40_000, float("inf")]
LOAN_AMOUNT_LABELS = ["<$10k", "$10–20k", "$20–30k", "$30–40k", ">$40k"]

INCOME_BINS   = [0, 40_000, 60_000, 80_000, 100_000, float("inf")]
INCOME_LABELS = ["<$40k", "$40–60k", "$60–80k", "$80–100k", ">$100k"]

INT_RATE_BINS   = [0, 8, 12, 16, 20, 24, float("inf")]
INT_RATE_LABELS = ["<8%", "8–12%", "12–16%", "16–20%", "20–24%", ">24%"]
