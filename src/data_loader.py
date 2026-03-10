"""
Data loading pipeline: CSV (Kaggle) or synthetic → feature engineering → SQLite.

Public API
----------
build_database()
    Idempotent entry-point called by scripts/setup.py.
    Detects whether the real Kaggle CSV is present; falls back to synthetic
    data if not.  Adds all derived columns needed by the dashboard and SQL
    queries, then writes to SQLite.
"""

import sqlite3
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    DB_PATH,
    LENDING_CLUB_CSV,
    DEFAULT_STATUSES,
    LOAN_AMOUNT_BINS, LOAN_AMOUNT_LABELS,
    INCOME_BINS, INCOME_LABELS,
    INT_RATE_BINS, INT_RATE_LABELS,
)
from src.data_generator import generate_synthetic_loans

logger = logging.getLogger(__name__)

# ─── Columns we need from the raw Kaggle CSV ─────────────────────────────────
_REQUIRED_COLS = [
    "loan_amnt", "funded_amnt", "term", "int_rate", "installment",
    "grade", "sub_grade", "emp_length", "home_ownership", "annual_inc",
    "loan_status", "purpose", "dti", "delinq_2yrs", "fico_range_low",
    "fico_range_high", "issue_d", "addr_state", "open_acc", "pub_rec",
    "revol_bal", "revol_util", "total_acc",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _load_kaggle_csv(path: Path, sample_n: int = 300_000) -> pd.DataFrame:
    """Load the Lending Club CSV and select relevant columns."""
    logger.info("Loading Kaggle CSV from %s …", path)
    df = pd.read_csv(path, low_memory=False, usecols=lambda c: c in _REQUIRED_COLS)

    missing = set(_REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    # Sample if very large
    if len(df) > sample_n:
        df = df.sample(sample_n, random_state=42)
        logger.info("Sampled %d rows from %d total.", sample_n, len(df))

    df = df.reset_index(drop=True)
    df.insert(0, "loan_id", df.index + 1)

    # Strip '%' suffix from int_rate if present
    if df["int_rate"].dtype == object:
        df["int_rate"] = df["int_rate"].str.rstrip("%").astype(float)

    return df


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns required by the dashboard and SQL queries."""
    df = df.copy()

    # ── Default flag ──────────────────────────────────────────────────────────
    df["is_default"] = df["loan_status"].isin(DEFAULT_STATUSES).astype(int)

    # ── Loan amount bucket ────────────────────────────────────────────────────
    df["loan_amnt_bucket"] = pd.cut(
        df["loan_amnt"],
        bins=LOAN_AMOUNT_BINS,
        labels=LOAN_AMOUNT_LABELS,
        right=True,
    ).astype(str)

    # ── Annual income bracket ─────────────────────────────────────────────────
    df["income_bracket"] = pd.cut(
        df["annual_inc"],
        bins=INCOME_BINS,
        labels=INCOME_LABELS,
        right=True,
    ).astype(str)

    # ── Interest rate bucket ──────────────────────────────────────────────────
    df["int_rate_bucket"] = pd.cut(
        df["int_rate"],
        bins=INT_RATE_BINS,
        labels=INT_RATE_LABELS,
        right=True,
    ).astype(str)

    # ── Date parts ────────────────────────────────────────────────────────────
    parsed = pd.to_datetime(df["issue_d"], format="%b-%Y", errors="coerce")
    df["issue_year"]       = parsed.dt.year.astype("Int64")
    df["issue_month"]      = parsed.dt.month.astype("Int64")
    df["issue_year_month"] = parsed.dt.to_period("M").astype(str)

    # ── FICO midpoint ─────────────────────────────────────────────────────────
    df["fico_mid"] = ((df["fico_range_low"] + df["fico_range_high"]) / 2).round(0)

    # ── Loan-to-income ratio ──────────────────────────────────────────────────
    df["lti"] = (df["loan_amnt"] / df["annual_inc"].replace(0, np.nan)).round(4)

    return df


def _write_to_sqlite(df: pd.DataFrame, db_path: Path) -> None:
    """Persist the DataFrame to SQLite and create performance indexes."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Writing %d rows to SQLite at %s …", len(df), db_path)

    with sqlite3.connect(db_path) as conn:
        df.to_sql("loans", conn, if_exists="replace", index=False, chunksize=50_000)

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_grade        ON loans(grade)",
            "CREATE INDEX IF NOT EXISTS idx_purpose      ON loans(purpose)",
            "CREATE INDEX IF NOT EXISTS idx_loan_status  ON loans(loan_status)",
            "CREATE INDEX IF NOT EXISTS idx_is_default   ON loans(is_default)",
            "CREATE INDEX IF NOT EXISTS idx_issue_year   ON loans(issue_year)",
            "CREATE INDEX IF NOT EXISTS idx_income       ON loans(income_bracket)",
            "CREATE INDEX IF NOT EXISTS idx_loan_bucket  ON loans(loan_amnt_bucket)",
            "CREATE INDEX IF NOT EXISTS idx_int_bucket   ON loans(int_rate_bucket)",
        ]
        for ddl in indexes:
            conn.execute(ddl)

    logger.info("Database ready.")


# ─── Public entry-point ───────────────────────────────────────────────────────

def build_database(force_rebuild: bool = False) -> None:
    """
    Build (or rebuild) the SQLite database.

    If *force_rebuild* is False and the DB already exists, this is a no-op.
    Data source priority:
      1. Kaggle CSV at data/raw/loan.csv
      2. Synthetic generator (fallback)
    """
    if DB_PATH.exists() and not force_rebuild:
        logger.info("Database already exists at %s. Skipping build.", DB_PATH)
        return

    if LENDING_CLUB_CSV.exists():
        df = _load_kaggle_csv(LENDING_CLUB_CSV)
    else:
        logger.warning(
            "Kaggle CSV not found at %s. "
            "Using synthetic data (%d records). "
            "To use real data, download from Kaggle and place it at the path above.",
            LENDING_CLUB_CSV,
            250_000,
        )
        df = generate_synthetic_loans()

    df = _engineer_features(df)
    _write_to_sqlite(df, DB_PATH)
