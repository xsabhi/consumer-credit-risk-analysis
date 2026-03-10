"""
Synthetic Lending Club-style dataset generator.

Produces statistically realistic consumer loan data that mirrors the structure
and distributional properties of the public Lending Club dataset.  Used when
the real Kaggle CSV is not present so the dashboard and analysis are always
runnable out-of-the-box.

Usage:
    from src.data_generator import generate_synthetic_loans
    df = generate_synthetic_loans(n=250_000)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.config import SYNTHETIC_RECORDS, RANDOM_SEED


# ─── Grade-level parameters ───────────────────────────────────────────────────
_GRADE_PARAMS = {
    #  grade : (base_default_rate, int_rate_low, int_rate_high, fico_low, fico_high)
    "A": (0.050, 5.0,  8.5,  760, 850),
    "B": (0.100, 8.5,  13.0, 720, 760),
    "C": (0.165, 13.0, 17.0, 690, 725),
    "D": (0.220, 17.0, 21.0, 660, 695),
    "E": (0.280, 21.0, 25.5, 625, 665),
    "F": (0.330, 25.5, 29.0, 600, 630),
    "G": (0.385, 29.0, 32.0, 580, 605),
}

_GRADE_DIST = dict(
    grades=list(_GRADE_PARAMS.keys()),
    probs=[0.20, 0.25, 0.22, 0.16, 0.10, 0.05, 0.02],
)

# ─── Purpose-level default-rate adjustments ──────────────────────────────────
_PURPOSE_ADJ = {
    "small_business":     +0.09,
    "moving":             +0.04,
    "other":              +0.03,
    "debt_consolidation": +0.02,
    "medical":            +0.02,
    "educational":        +0.01,
    "vacation":           +0.01,
    "wedding":            +0.01,
    "credit_card":         0.00,
    "major_purchase":     -0.02,
    "car":                -0.03,
    "home_improvement":   -0.04,
    "house":              -0.05,
}

_PURPOSE_DIST = dict(
    purposes=list(_PURPOSE_ADJ.keys()),
    probs=[0.04, 0.02, 0.08, 0.35, 0.05, 0.01, 0.03, 0.01, 0.20, 0.06, 0.03, 0.10, 0.02],
)

# ─── Loan amount choices (rounded to nearest $1k) ────────────────────────────
_LOAN_AMOUNTS = [
    1_000, 2_000, 3_000, 4_000, 5_000, 6_000, 7_000, 8_000, 9_000,
    10_000, 12_000, 15_000, 20_000, 25_000, 30_000, 35_000, 40_000,
]
_LOAN_AMOUNT_PROBS = [
    0.03, 0.04, 0.06, 0.05, 0.10, 0.05, 0.05, 0.04, 0.03,
    0.15, 0.08, 0.10, 0.08, 0.05, 0.04, 0.03, 0.02,
]

_US_STATES = [
    "CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
    "CO", "MN", "SC", "AL", "LA", "KY", "OR", "OK", "CT", "UT",
]


def generate_synthetic_loans(n: int = SYNTHETIC_RECORDS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Return a DataFrame of *n* synthetic consumer loans with realistic
    distributional properties, including correlated default behaviour.

    Parameters
    ----------
    n    : number of loan records to generate
    seed : NumPy random seed for reproducibility
    """
    rng = np.random.default_rng(seed)

    # ── Grade & interest rate ────────────────────────────────────────────────
    grade = rng.choice(_GRADE_DIST["grades"], size=n, p=_GRADE_DIST["probs"])

    int_rate = np.array([
        rng.uniform(_GRADE_PARAMS[g][1], _GRADE_PARAMS[g][2])
        for g in grade
    ]).round(2)

    # ── FICO scores (correlated with grade) ──────────────────────────────────
    fico_range_low = np.array([
        rng.integers(_GRADE_PARAMS[g][3], _GRADE_PARAMS[g][4])
        for g in grade
    ])
    fico_range_high = fico_range_low + rng.integers(4, 10, size=n)

    # ── Loan amount ──────────────────────────────────────────────────────────
    loan_amnt = rng.choice(_LOAN_AMOUNTS, size=n, p=_LOAN_AMOUNT_PROBS).astype(float)

    # ── Term ─────────────────────────────────────────────────────────────────
    term = rng.choice(["36 months", "60 months"], size=n, p=[0.70, 0.30])

    # ── Purpose ──────────────────────────────────────────────────────────────
    purpose = rng.choice(
        _PURPOSE_DIST["purposes"], size=n, p=_PURPOSE_DIST["probs"]
    )

    # ── Employment length ────────────────────────────────────────────────────
    emp_length = rng.choice(
        ["< 1 year", "1 year", "2 years", "3 years", "4 years", "5 years",
         "6 years", "7 years", "8 years", "9 years", "10+ years", "n/a"],
        size=n,
        p=[0.10, 0.08, 0.08, 0.07, 0.06, 0.07, 0.05, 0.05, 0.04, 0.03, 0.25, 0.12],
    )

    # ── Home ownership ───────────────────────────────────────────────────────
    home_ownership = rng.choice(
        ["RENT", "MORTGAGE", "OWN", "OTHER"], size=n, p=[0.45, 0.40, 0.13, 0.02]
    )

    # ── Annual income (log-normal, clipped to realistic range) ───────────────
    annual_inc = np.exp(rng.normal(loc=10.8, scale=0.6, size=n))
    annual_inc = np.clip(annual_inc, 10_000, 500_000).round(-2)

    # ── DTI ──────────────────────────────────────────────────────────────────
    dti = rng.uniform(0, 45, size=n).round(2)

    # ── Issue dates (2014–2020) ───────────────────────────────────────────────
    start_ts = datetime(2014, 1, 1)
    day_offsets = rng.integers(0, (datetime(2020, 12, 31) - start_ts).days, size=n)
    issue_dates = [start_ts + timedelta(days=int(d)) for d in day_offsets]
    issue_d = [d.strftime("%b-%Y") for d in issue_dates]

    # ── Default probability (multi-factor model) ─────────────────────────────
    base_prob = np.array([_GRADE_PARAMS[g][0] for g in grade])

    # Purpose adjustment
    base_prob += np.array([_PURPOSE_ADJ.get(p, 0.0) for p in purpose])

    # Income factor: higher income → lower default probability
    income_factor = np.clip(1.0 - (annual_inc - 50_000) / 600_000, 0.70, 1.35)
    base_prob *= income_factor

    # DTI factor: higher DTI → higher default probability
    dti_factor = 1.0 + (dti - 20.0) / 100.0
    base_prob *= dti_factor

    # Employment stability adjustment
    emp_adj = {
        "10+ years": -0.02, "n/a": +0.04, "< 1 year": +0.03,
    }
    base_prob += np.array([emp_adj.get(e, 0.0) for e in emp_length])

    base_prob = np.clip(base_prob, 0.02, 0.60)

    # Assign loan status
    is_default = rng.random(n) < base_prob
    default_statuses  = ["Charged Off", "Default", "Late (31-120 days)"]
    current_statuses  = ["Fully Paid", "Current"]

    loan_status = np.where(
        is_default,
        rng.choice(default_statuses, size=n, p=[0.70, 0.20, 0.10]),
        rng.choice(current_statuses, size=n, p=[0.60, 0.40]),
    )

    # ── Other credit bureau fields ────────────────────────────────────────────
    delinq_2yrs = rng.choice([0, 1, 2, 3, 4, 5], size=n,
                              p=[0.70, 0.15, 0.07, 0.04, 0.02, 0.02])
    open_acc    = rng.integers(2, 30, size=n)
    pub_rec     = rng.choice([0, 1, 2], size=n, p=[0.85, 0.12, 0.03])
    revol_bal   = np.exp(rng.normal(8.5, 1.0, size=n)).round(0)
    revol_util  = rng.uniform(0, 100, size=n).round(1)
    total_acc   = open_acc + rng.integers(0, 20, size=n)
    addr_state  = rng.choice(_US_STATES, size=n)

    # Sub-grade (e.g. B3)
    sub_grade = np.array([g + str(rng.integers(1, 6)) for g in grade])

    # Monthly installment (simplified annuity formula)
    monthly_rate = (int_rate / 100) / 12
    months = np.where(term == "36 months", 36, 60)
    installment = (
        loan_amnt * monthly_rate / (1 - (1 + monthly_rate) ** (-months))
    ).round(2)

    return pd.DataFrame({
        "loan_id":         np.arange(1, n + 1),
        "loan_amnt":       loan_amnt,
        "funded_amnt":     loan_amnt,
        "term":            term,
        "int_rate":        int_rate,
        "installment":     installment,
        "grade":           grade,
        "sub_grade":       sub_grade,
        "emp_length":      emp_length,
        "home_ownership":  home_ownership,
        "annual_inc":      annual_inc,
        "loan_status":     loan_status,
        "purpose":         purpose,
        "dti":             dti,
        "delinq_2yrs":     delinq_2yrs,
        "fico_range_low":  fico_range_low,
        "fico_range_high": fico_range_high,
        "issue_d":         issue_d,
        "addr_state":      addr_state,
        "open_acc":        open_acc,
        "pub_rec":         pub_rec,
        "revol_bal":       revol_bal,
        "revol_util":      revol_util,
        "total_acc":       total_acc,
    })
