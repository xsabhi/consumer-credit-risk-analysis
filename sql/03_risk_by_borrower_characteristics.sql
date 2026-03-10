-- =============================================================================
-- CONSUMER CREDIT PORTFOLIO RISK ANALYSIS
-- Query Set 3: Risk by Borrower Characteristics
-- Author : Abhishek Dharwadkar
-- Purpose: Profile which borrower segments present the highest default risk
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 3.1  Default rate by income bracket
--      Key underwriting signal; higher income strongly predicts lower default.
-- -----------------------------------------------------------------------------
SELECT
    income_bracket,
    COUNT(*)                                AS loan_count,
    ROUND(AVG(annual_inc), 0)               AS avg_annual_income,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
WHERE income_bracket IS NOT NULL
  AND income_bracket != 'nan'
GROUP BY income_bracket
ORDER BY
    CASE income_bracket
        WHEN '<$40k'    THEN 1
        WHEN '$40–60k'  THEN 2
        WHEN '$60–80k'  THEN 3
        WHEN '$80–100k' THEN 4
        WHEN '>$100k'   THEN 5
        ELSE 6
    END;


-- -----------------------------------------------------------------------------
-- 3.2  Default rate by employment length
--      Proxy for job stability; longer tenure typically correlates with lower risk.
-- -----------------------------------------------------------------------------
SELECT
    emp_length,
    COUNT(*)                                AS loan_count,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
WHERE emp_length IS NOT NULL
  AND emp_length != 'n/a'
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
    END;


-- -----------------------------------------------------------------------------
-- 3.3  Default rate by home ownership status
-- -----------------------------------------------------------------------------
SELECT
    home_ownership,
    COUNT(*)                                AS loan_count,
    ROUND(AVG(annual_inc), 0)               AS avg_annual_income,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY home_ownership
ORDER BY default_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- 3.4  Default rate by delinquency history
--      Prior delinquencies are a strong predictor of future defaults.
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN delinq_2yrs = 0 THEN '0 delinquencies'
        WHEN delinq_2yrs = 1 THEN '1 delinquency'
        WHEN delinq_2yrs = 2 THEN '2 delinquencies'
        ELSE '3+ delinquencies'
    END                                     AS delinquency_group,
    COUNT(*)                                AS loan_count,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY delinquency_group
ORDER BY
    CASE delinquency_group
        WHEN '0 delinquencies'  THEN 1
        WHEN '1 delinquency'    THEN 2
        WHEN '2 delinquencies'  THEN 3
        WHEN '3+ delinquencies' THEN 4
    END;


-- -----------------------------------------------------------------------------
-- 3.5  High-risk borrower segment identification (CTE + window functions)
--      Ranks income brackets by default rate within each grade.
--      Useful for targeted underwriting policy changes.
-- -----------------------------------------------------------------------------
WITH segment_stats AS (
    SELECT
        grade,
        income_bracket,
        COUNT(*)                            AS loan_count,
        ROUND(100.0 * SUM(is_default)
              / COUNT(*), 2)                AS default_rate_pct,
        ROUND(AVG(loan_amnt), 0)            AS avg_loan_amnt
    FROM loans
    WHERE income_bracket IS NOT NULL
      AND income_bracket != 'nan'
    GROUP BY grade, income_bracket
    HAVING COUNT(*) >= 100
),
ranked AS (
    SELECT *,
        RANK() OVER (
            PARTITION BY grade
            ORDER BY default_rate_pct DESC
        )                                   AS risk_rank_within_grade
    FROM segment_stats
)
SELECT *
FROM ranked
WHERE risk_rank_within_grade = 1
ORDER BY default_rate_pct DESC;
