"""
One-time project setup script.

Run this first after cloning the repo:
    python scripts/setup.py

What it does
------------
1. Creates required directories.
2. Builds the SQLite database (synthetic data if Kaggle CSV is absent).
3. Validates the database by running a quick sanity check.
4. Prints a summary with instructions for next steps.
"""

import sys
import logging
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_directories() -> None:
    dirs = [
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "reports" / "output",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directories OK.")


def build_db() -> None:
    from src.data_loader import build_database
    build_database(force_rebuild=False)


def validate_db() -> None:
    from src.database import row_count, table_exists, query

    assert table_exists("loans"), "Table 'loans' not found!"
    n = row_count("loans")
    assert n > 0, "Table 'loans' is empty!"
    logger.info("Database has %s rows.", f"{n:,}")

    # Check derived columns exist
    sample = query("SELECT is_default, loan_amnt_bucket, income_bracket, "
                   "int_rate_bucket, issue_year FROM loans LIMIT 1")
    assert not sample.empty, "Could not read derived columns."

    # Quick default rate sanity check
    kpi = query("SELECT ROUND(100.0*SUM(is_default)/COUNT(*),2) AS dr FROM loans")
    dr = float(kpi["dr"].iloc[0])
    logger.info("Portfolio default rate: %.2f%%", dr)
    assert 2 <= dr <= 60, f"Default rate out of expected range: {dr}"

    logger.info("Validation passed ✓")


def print_next_steps() -> None:
    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Launch the dashboard:")
    print("       streamlit run dashboard/app.py")
    print()
    print("  2. (Optional) Use real Kaggle data:")
    print("       • Download 'Lending Club Loan Data' from Kaggle")
    print("       • Place loan.csv in  data/raw/loan.csv")
    print("       • Re-run:  python scripts/setup.py --rebuild")
    print()
    print("  3. Generate the PDF report:")
    print("       python reports/generate_report.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv

    logger.info("Starting project setup …")
    create_directories()

    if rebuild:
        from src.config import DB_PATH
        if DB_PATH.exists():
            DB_PATH.unlink()
            logger.info("Existing database removed for rebuild.")

    build_db()
    validate_db()
    print_next_steps()
