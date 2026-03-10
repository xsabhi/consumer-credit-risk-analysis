"""
Core analysis functions used by both the dashboard and the report generator.

Each function returns a clean DataFrame ready for charting or tabulation.
All heavy lifting is done in SQL so the database engine handles performance.
"""

from typing import Optional, List
import pandas as pd
from src.database import query


# ─── Helper ──────────────────────────────────────────────────────────────────

def _grade_filter(grades: Optional[List[str]]) -> str:
    """Build a SQL IN clause for grade filtering, or empty string."""
    if grades and len(grades) < 7:
        formatted = ", ".join(f"'{g}'" for g in grades)
        return f"AND grade IN ({formatted})"
    return ""


def _year_filter(year_range: Optional[tuple]) -> str:
    if year_range:
        return f"AND issue_year BETWEEN {year_range[0]} AND {year_range[1]}"
    return ""


def _purpose_filter(purposes: Optional[List[str]]) -> str:
    if purposes and len(purposes) < 13:
        formatted = ", ".join(f"'{p}'" for p in purposes)
        return f"AND purpose IN ({formatted})"
    return ""


# ─── Portfolio Overview ───────────────────────────────────────────────────────

def portfolio_kpis(grades=None, year_range=None, purposes=None) -> dict:
    """Return top-level KPI scalars."""
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)

    df = query(f"""
        SELECT
            COUNT(*)                          AS total_loans,
            SUM(loan_amnt)                    AS total_volume,
            AVG(loan_amnt)                    AS avg_loan_size,
            ROUND(AVG(is_default) * 100, 2)   AS default_rate_pct,
            AVG(int_rate)                     AS avg_int_rate,
            AVG(annual_inc)                   AS avg_income,
            AVG(dti)                          AS avg_dti
        FROM loans
        WHERE 1=1 {gf} {yf} {pf}
    """)
    return df.iloc[0].to_dict()


def loans_by_grade(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            grade,
            COUNT(*)                        AS loan_count,
            SUM(loan_amnt)                  AS total_volume,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        WHERE 1=1 {gf} {yf} {pf}
        GROUP BY grade
        ORDER BY grade
    """)


def loans_by_purpose(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            purpose,
            COUNT(*)                        AS loan_count,
            SUM(loan_amnt)                  AS total_volume,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        WHERE 1=1 {gf} {yf} {pf}
        GROUP BY purpose
        ORDER BY default_rate DESC
    """)


def loans_by_status(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            loan_status,
            COUNT(*) AS loan_count
        FROM loans
        WHERE 1=1 {gf} {yf} {pf}
        GROUP BY loan_status
        ORDER BY loan_count DESC
    """)


# ─── Risk Analysis ────────────────────────────────────────────────────────────

def default_by_loan_amount_bucket(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            loan_amnt_bucket,
            COUNT(*)                        AS loan_count,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        WHERE loan_amnt_bucket != 'nan'
          {gf} {yf} {pf}
        GROUP BY loan_amnt_bucket
        ORDER BY
            CASE loan_amnt_bucket
                WHEN '<$10k'    THEN 1
                WHEN '$10–20k'  THEN 2
                WHEN '$20–30k'  THEN 3
                WHEN '$30–40k'  THEN 4
                WHEN '>$40k'    THEN 5
                ELSE 6
            END
    """)


def default_by_int_rate_bucket(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            int_rate_bucket,
            COUNT(*)                        AS loan_count,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        WHERE int_rate_bucket != 'nan'
          {gf} {yf} {pf}
        GROUP BY int_rate_bucket
        ORDER BY
            CASE int_rate_bucket
                WHEN '<8%'    THEN 1
                WHEN '8–12%'  THEN 2
                WHEN '12–16%' THEN 3
                WHEN '16–20%' THEN 4
                WHEN '20–24%' THEN 5
                WHEN '>24%'   THEN 6
                ELSE 7
            END
    """)


def default_by_income_bracket(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            income_bracket,
            COUNT(*)                        AS loan_count,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        WHERE income_bracket != 'nan'
          {gf} {yf} {pf}
        GROUP BY income_bracket
        ORDER BY
            CASE income_bracket
                WHEN '<$40k'    THEN 1
                WHEN '$40–60k'  THEN 2
                WHEN '$60–80k'  THEN 3
                WHEN '$80–100k' THEN 4
                WHEN '>$100k'   THEN 5
                ELSE 6
            END
    """)


def default_by_emp_length(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            emp_length,
            COUNT(*)                        AS loan_count,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        WHERE emp_length != 'n/a'
          {gf} {yf} {pf}
        GROUP BY emp_length
        ORDER BY
            CASE emp_length
                WHEN '< 1 year'  THEN 1
                WHEN '1 year'    THEN 2
                WHEN '2 years'   THEN 3
                WHEN '3 years'   THEN 4
                WHEN '4 years'   THEN 5
                WHEN '5 years'   THEN 6
                WHEN '6 years'   THEN 7
                WHEN '7 years'   THEN 8
                WHEN '8 years'   THEN 9
                WHEN '9 years'   THEN 10
                WHEN '10+ years' THEN 11
                ELSE 12
            END
    """)


# ─── Risk Heatmap ────────────────────────────────────────────────────────────

def heatmap_grade_purpose(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    """Default rate by grade × purpose, pivoted for heatmap rendering."""
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    df = query(f"""
        SELECT
            grade,
            purpose,
            ROUND(AVG(is_default)*100, 2) AS default_rate
        FROM loans
        WHERE 1=1 {gf} {yf} {pf}
        GROUP BY grade, purpose
    """)
    return df.pivot(index="purpose", columns="grade", values="default_rate").fillna(0)


def heatmap_income_loan_bucket(grades=None, year_range=None, purposes=None) -> pd.DataFrame:
    """Default rate by income bracket × loan amount bucket, pivoted."""
    gf = _grade_filter(grades)
    yf = _year_filter(year_range)
    pf = _purpose_filter(purposes)
    df = query(f"""
        SELECT
            income_bracket,
            loan_amnt_bucket,
            ROUND(AVG(is_default)*100, 2) AS default_rate
        FROM loans
        WHERE income_bracket != 'nan'
          AND loan_amnt_bucket != 'nan'
          {gf} {yf} {pf}
        GROUP BY income_bracket, loan_amnt_bucket
    """)
    pivot = df.pivot(
        index="income_bracket", columns="loan_amnt_bucket", values="default_rate"
    ).fillna(0)

    row_order = ["<$40k", "$40–60k", "$60–80k", "$80–100k", ">$100k"]
    col_order = ["<$10k", "$10–20k", "$20–30k", "$30–40k", ">$40k"]
    pivot = pivot.reindex(
        index=[r for r in row_order if r in pivot.index],
        columns=[c for c in col_order if c in pivot.columns],
    )
    return pivot


# ─── Time / Vintage Trends ───────────────────────────────────────────────────

def monthly_originations(grades=None, purposes=None) -> pd.DataFrame:
    """Monthly loan count and volume over time."""
    gf = _grade_filter(grades)
    pf = _purpose_filter(purposes)
    return query(f"""
        SELECT
            issue_year_month,
            issue_year,
            issue_month,
            COUNT(*)        AS loan_count,
            SUM(loan_amnt)  AS total_volume,
            ROUND(AVG(is_default)*100, 2) AS default_rate
        FROM loans
        WHERE issue_year_month IS NOT NULL
          AND issue_year_month != 'NaT'
          {gf} {pf}
        GROUP BY issue_year_month, issue_year, issue_month
        ORDER BY issue_year, issue_month
    """)


def vintage_default_rates() -> pd.DataFrame:
    """Annual default rate by origination vintage."""
    return query("""
        SELECT
            issue_year                      AS vintage,
            COUNT(*)                        AS loan_count,
            ROUND(AVG(is_default)*100, 2)   AS default_rate,
            AVG(int_rate)                   AS avg_int_rate,
            AVG(loan_amnt)                  AS avg_loan_amnt
        FROM loans
        WHERE issue_year IS NOT NULL
        GROUP BY issue_year
        ORDER BY issue_year
    """)


# ─── State-level map data ─────────────────────────────────────────────────────

def default_by_state() -> pd.DataFrame:
    return query("""
        SELECT
            addr_state,
            COUNT(*)                        AS loan_count,
            ROUND(AVG(is_default)*100, 2)   AS default_rate
        FROM loans
        GROUP BY addr_state
        ORDER BY default_rate DESC
    """)
