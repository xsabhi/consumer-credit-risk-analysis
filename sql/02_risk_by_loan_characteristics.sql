-- =============================================================================
-- CONSUMER CREDIT PORTFOLIO RISK ANALYSIS
-- Query Set 2: Risk by Loan Characteristics
-- Author : Abhishek Dharwadkar
-- Purpose: Identify which loan attributes drive elevated default rates
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 2.1  Default rate by loan purpose
--      Helps underwriting teams price risk and set origination limits.
-- -----------------------------------------------------------------------------
SELECT
    purpose,
    COUNT(*)                                AS loan_count,
    SUM(loan_amnt)                          AS total_volume,
    ROUND(AVG(loan_amnt), 0)                AS avg_loan_size,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY purpose
ORDER BY default_rate_pct DESC;


-- -----------------------------------------------------------------------------
-- 2.2  Default rate by loan amount bucket
--      Identifies whether larger loans carry disproportionate risk.
-- -----------------------------------------------------------------------------
SELECT
    loan_amnt_bucket,
    COUNT(*)                                AS loan_count,
    ROUND(AVG(loan_amnt), 0)                AS avg_loan_size,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
WHERE loan_amnt_bucket IS NOT NULL
  AND loan_amnt_bucket != 'nan'
GROUP BY loan_amnt_bucket
ORDER BY
    CASE loan_amnt_bucket
        WHEN '<$10k'   THEN 1
        WHEN '$10–20k' THEN 2
        WHEN '$20–30k' THEN 3
        WHEN '$30–40k' THEN 4
        WHEN '>$40k'   THEN 5
        ELSE 6
    END;


-- -----------------------------------------------------------------------------
-- 2.3  Default rate by interest rate bucket
--      Tests whether adverse selection exists at high rates.
-- -----------------------------------------------------------------------------
SELECT
    int_rate_bucket,
    COUNT(*)                                AS loan_count,
    ROUND(AVG(int_rate), 2)                 AS avg_int_rate,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
WHERE int_rate_bucket IS NOT NULL
  AND int_rate_bucket != 'nan'
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
    END;


-- -----------------------------------------------------------------------------
-- 2.4  Default rate by term
-- -----------------------------------------------------------------------------
SELECT
    term,
    COUNT(*)                                AS loan_count,
    ROUND(AVG(int_rate), 2)                 AS avg_int_rate,
    ROUND(100.0 * SUM(is_default)
          / COUNT(*), 2)                    AS default_rate_pct
FROM loans
GROUP BY term;


-- -----------------------------------------------------------------------------
-- 2.5  High-risk loan segments (purpose × grade)
--      CTE pattern: identify combinations with default rate > 25%
-- -----------------------------------------------------------------------------
WITH risk_segments AS (
    SELECT
        grade,
        purpose,
        COUNT(*)                            AS loan_count,
        ROUND(100.0 * SUM(is_default)
              / COUNT(*), 2)                AS default_rate_pct
    FROM loans
    GROUP BY grade, purpose
    HAVING COUNT(*) >= 50          -- min segment size for statistical stability
)
SELECT *
FROM risk_segments
WHERE default_rate_pct >= 25.0
ORDER BY default_rate_pct DESC
LIMIT 20;
