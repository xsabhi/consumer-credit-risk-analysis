# Consumer Credit Portfolio Risk Analysis

An end-to-end credit risk analytics project analysing consumer loan performance across credit grades, borrower segments, and origination vintages using SQL, Python, and an interactive Streamlit dashboard.

**Author:** Abhishek Dharwadkar
**Dataset:** Lending Club Public Loan Data (Kaggle) · 250k+ consumer loans · 2014–2020
**Stack:** Python · SQLite · Streamlit · Plotly · ReportLab

---

## Overview

This project explores the question: *which loans are most likely to default, and why?* Using the Lending Club public dataset, it segments a portfolio of 250,000+ consumer loans by credit grade, loan purpose, borrower income, employment history, and origination vintage to surface default risk patterns and underwriting insights.

---

## Project Structure

```
consumer-credit-risk-analysis/
├── dashboard/
│   └── app.py                  ← Streamlit dashboard
├── src/
│   ├── config.py               ← Paths, thresholds, bin definitions
│   ├── data_generator.py       ← Synthetic Lending Club data (250k rows)
│   ├── data_loader.py          ← CSV → feature engineering → SQLite
│   ├── database.py             ← SQLite connection helpers
│   └── analysis.py             ← Core analysis functions
├── sql/
│   ├── 01_portfolio_overview.sql
│   ├── 02_risk_by_loan_characteristics.sql
│   ├── 03_risk_by_borrower_characteristics.sql
│   └── 04_time_based_analysis.sql
├── reports/
│   ├── generate_report.py      ← PDF report generator
│   └── output/                 ← Generated PDF lands here
├── scripts/
│   └── setup.py                ← One-time database setup
├── data/
│   └── raw/                    ← Place loan.csv here (see below)
├── requirements.txt
└── .streamlit/config.toml      ← Dashboard theme
```

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/xsabhi/consumer-credit-risk-analysis.git
cd consumer-credit-risk-analysis

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up the database

```bash
python scripts/setup.py
```

This builds a SQLite database using **synthetic data** (250,000 realistic consumer loans) so the dashboard runs immediately without downloading anything.

> **To use the real Lending Club dataset:**
> 1. Download from Kaggle: [Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club)
> 2. Place `loan.csv` in `data/raw/loan.csv`
> 3. Rebuild: `python scripts/setup.py --rebuild`

### 3. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Generate the PDF report

```bash
python reports/generate_report.py
```

Output: `reports/output/Consumer_Credit_Risk_Analysis_Abhishek_Dharwadkar.pdf`

---

## Dashboard

The dashboard has **5 tabs**, with sidebar filters for credit grade, origination year, and loan purpose that update all charts in real time.

| Tab | Contents |
|---|---|
| Portfolio Overview | KPI tiles, loan volume by grade, status breakdown, origination by purpose |
| Default Analysis | Default rates by loan amount, interest rate, income, employment length, purpose |
| Risk Heatmaps | Grade × Purpose heatmap, Income × Loan Amount heatmap, US state choropleth |
| Vintage Trends | Monthly originations, default rate trend, vintage cohort analysis |
| SQL Explorer | Live SQL console with preset queries |

---

## SQL

Four query files covering portfolio overview, loan risk, borrower risk, and time-based analysis. Key techniques used:

- `GROUP BY` segmentation with aggregate functions (`COUNT`, `SUM`, `AVG`)
- `CASE` statements for custom ordering of bucketed categories
- CTEs to identify high-risk grade × purpose segments above a 25% default threshold
- Window functions — `RANK() OVER (PARTITION BY ...)` for within-grade risk ranking, `LAG()` for year-over-year default rate change, and a 3-month rolling average with `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`

---

## Key Findings

- **Grade is the strongest predictor of default:** rates range from ~6% (Grade A) to ~40% (Grade G)
- **Small business loans carry the highest default rate by purpose** (~26%), roughly 2.5x that of home improvement loans (~10%)
- **Income is inversely correlated with default:** borrowers earning under $40k default at ~22% vs ~12% for those earning over $100k
- **Adverse selection at high interest rates:** loans priced above 24% default at ~4x the rate of sub-8% loans
- **Portfolio default rate of ~17%** is driven primarily by Grade D–G originations and small business loans

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo, set main file path to `dashboard/app.py`
4. Click Deploy

The app auto-generates the database on first launch using synthetic data.

---

## Contact

**Abhishek Dharwadkar**
[LinkedIn](https://linkedin.com/in/abhishekvdharwadkar) · [GitHub](https://github.com/xsabhi)