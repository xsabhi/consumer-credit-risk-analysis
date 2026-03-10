-- =============================================================================
-- CONSUMER CREDIT PORTFOLIO RISK ANALYSIS
-- Query Set 1: Portfolio Overview
-- Author : Abhishek Dharwadkar
-- Purpose: Provide high-level portfolio metrics for executive reporting
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1.1  Top-level KPIs
--      Returns a single summary row suitable for a dashboard KPI tile.
-- -----------------------------------------------------------------------------
SELECT
    COUNT(*)                                AS total_loans,
    SUM(loan_amnt)                          AS total_loan_volume,
    AVG(loan_amnt)                          AS avg_loan_size,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct,
    AVG(int_rate)                           AS avg_interest_rate,
    AVG(annual_inc)                         AS avg_borrower_income,
    AVG(dti)                                AS avg_debt_to_income
FROM loans;


-- -----------------------------------------------------------------------------
-- 1.2  Loan count and volume by credit grade
--      Shows portfolio composition and per-grade risk profile.
-- -----------------------------------------------------------------------------
SELECT
    grade,
    COUNT(*)                                AS loan_count,
    SUM(loan_amnt)                          AS total_volume,
    ROUND(AVG(loan_amnt), 0)                AS avg_loan_size,
    ROUND(AVG(int_rate), 2)                 AS avg_int_rate,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY grade
ORDER BY grade;


-- -----------------------------------------------------------------------------
-- 1.3  Loan status breakdown
--      Current, Fully Paid, Charged Off, etc.
-- -----------------------------------------------------------------------------
SELECT
    loan_status,
    COUNT(*)                                AS loan_count,
    ROUND(100.0 * COUNT(*)
          / SUM(COUNT(*)) OVER (), 2)       AS pct_of_portfolio,
    SUM(loan_amnt)                          AS total_volume
FROM loans
GROUP BY loan_status
ORDER BY loan_count DESC;


-- -----------------------------------------------------------------------------
-- 1.4  Term split (36-month vs 60-month)
-- -----------------------------------------------------------------------------
SELECT
    term,
    COUNT(*)                                AS loan_count,
    ROUND(AVG(loan_amnt), 0)                AS avg_loan_size,
    ROUND(AVG(int_rate), 2)                 AS avg_int_rate,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY term;


-- -----------------------------------------------------------------------------
-- 1.5  Top 10 states by loan volume
-- -----------------------------------------------------------------------------
SELECT
    addr_state                              AS state,
    COUNT(*)                                AS loan_count,
    SUM(loan_amnt)                          AS total_volume,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY addr_state
ORDER BY total_volume DESC
LIMIT 10;
