-- =============================================================================
-- CONSUMER CREDIT PORTFOLIO RISK ANALYSIS
-- Query Set 4: Time-Based & Vintage Analysis
-- Author : Abhishek Dharwadkar
-- Purpose: Detect trends in portfolio risk over time and by origination cohort
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 4.1  Monthly origination volume and default rate trend
--      Reveals seasonality and whether credit quality is improving or deteriorating.
-- -----------------------------------------------------------------------------
SELECT
    issue_year_month,
    issue_year,
    issue_month,
    COUNT(*)                                AS loan_count,
    SUM(loan_amnt)                          AS total_volume,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct,
    -- 3-month rolling average default rate (window function)
    ROUND(
        AVG(ROUND(100.0 * SUM(is_default) / COUNT(*), 2))
        OVER (
            ORDER BY issue_year, issue_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 2
    )                                       AS rolling_3m_default_rate
FROM loans
WHERE issue_year_month IS NOT NULL
  AND issue_year_month != 'NaT'
GROUP BY issue_year_month, issue_year, issue_month
ORDER BY issue_year, issue_month;


-- -----------------------------------------------------------------------------
-- 4.2  Vintage analysis – annual cohort default rates
--      Answers: "Are loans originated in year X performing worse than prior years?"
-- -----------------------------------------------------------------------------
SELECT
    issue_year                              AS vintage_year,
    COUNT(*)                                AS loans_originated,
    SUM(loan_amnt)                          AS total_volume,
    ROUND(AVG(loan_amnt), 0)                AS avg_loan_size,
    ROUND(AVG(int_rate), 2)                 AS avg_int_rate,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct,
    -- Year-over-year change in default rate (window function)
    ROUND(
        ROUND(100.0 * SUM(is_default) / COUNT(*), 2)
        - LAG(ROUND(100.0 * SUM(is_default) / COUNT(*), 2))
          OVER (ORDER BY issue_year), 2
    )                                       AS yoy_default_rate_change
FROM loans
WHERE issue_year IS NOT NULL
GROUP BY issue_year
ORDER BY issue_year;


-- -----------------------------------------------------------------------------
-- 4.3  Vintage × Grade cross-tab
--      Identifies which grade deteriorated most in recent vintages.
-- -----------------------------------------------------------------------------
SELECT
    issue_year,
    grade,
    COUNT(*)                                AS loan_count,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
WHERE issue_year IS NOT NULL
GROUP BY issue_year, grade
ORDER BY issue_year, grade;


-- -----------------------------------------------------------------------------
-- 4.4  Monthly default rate by purpose (top 5 purposes only)
--      Detects whether specific purpose categories are trending worse over time.
-- -----------------------------------------------------------------------------
WITH top_purposes AS (
    SELECT purpose
    FROM loans
    GROUP BY purpose
    ORDER BY COUNT(*) DESC
    LIMIT 5
)
SELECT
    l.issue_year,
    l.issue_month,
    l.issue_year_month,
    l.purpose,
    COUNT(*)                                AS loan_count,
    ROUND(100.0 * SUM(l.is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans l
JOIN top_purposes tp ON l.purpose = tp.purpose
WHERE l.issue_year_month IS NOT NULL
  AND l.issue_year_month != 'NaT'
GROUP BY l.issue_year, l.issue_month, l.issue_year_month, l.purpose
ORDER BY l.issue_year, l.issue_month, l.purpose;
