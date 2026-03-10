# Consumer Credit Portfolio Risk Analysis

An end-to-end credit risk analytics project demonstrating SQL segmentation, Python analysis, and an interactive Streamlit dashboard — targeting analyst roles at Capital One, Goldman Sachs, Citi, and Self Financial.

**Author:** Abhishek Dharwadkar
**Dataset:** Lending Club Public Loan Data (Kaggle) · 250k+ consumer loans · 2014–2020
**Stack:** Python · SQLite · Streamlit · Plotly · ReportLab

---

## What This Project Demonstrates

| Skill | Implementation |
|---|---|
| SQL for data analysis | 4 query files with CTEs, window functions, GROUP BY segmentation |
| Python data analysis | Pandas feature engineering, multi-factor default model |
| Dashboard / visualisation | Streamlit + Plotly interactive dashboard with filters |
| Credit risk domain knowledge | Default rate segmentation, vintage analysis, underwriting insights |
| Communication of insights | 2-page executive PDF report |

---

## Project Structure

```
consumer-credit-risk-analysis/
├── dashboard/
│   └── app.py                  ← Streamlit dashboard (main deliverable)
├── src/
│   ├── config.py               ← Paths, thresholds, bin definitions
│   ├── data_generator.py       ← Synthetic Lending Club data (250k rows)
│   ├── data_loader.py          ← CSV → feature engineering → SQLite
│   ├── database.py             ← SQLite connection helpers
│   └── analysis.py             ← All analysis queries used by dashboard
├── sql/
│   ├── 01_portfolio_overview.sql
│   ├── 02_risk_by_loan_characteristics.sql
│   ├── 03_risk_by_borrower_characteristics.sql
│   └── 04_time_based_analysis.sql
├── reports/
│   ├── generate_report.py      ← PDF report generator (ReportLab)
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
git clone https://github.com/yourusername/consumer-credit-risk-analysis.git
cd consumer-credit-risk-analysis
pip install -r requirements.txt
```

### 2. Set up the database

```bash
python scripts/setup.py
```

This builds a SQLite database using **synthetic data** (250,000 realistic consumer loans) so you can run the dashboard immediately without downloading anything.

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

## Dashboard Features

The dashboard has **5 tabs**:

| Tab | Contents |
|---|---|
| Portfolio Overview | KPI tiles, loan volume by grade, status donut, origination by purpose |
| Default Analysis | Default rates by loan amount, interest rate, income, employment length, purpose |
| Risk Heatmaps | Grade × Purpose heatmap, Income × Loan Amount heatmap, US state choropleth |
| Vintage Trends | Monthly originations, default rate trend, vintage cohort analysis |
| SQL Explorer | Live SQL console against the credit database with preset queries |

**Sidebar filters:** Credit grade, origination year range, loan purpose — all charts update in real-time.

---

## SQL Highlights

Four query files covering the key analytical questions hiring managers care about:

- **Portfolio overview**: KPIs, grade composition, status breakdown, state-level volume
- **Loan risk**: Default rates by purpose, loan amount bucket, interest rate band — including CTE to identify grade × purpose segments with >25% default rates
- **Borrower risk**: Default rates by income, employment length, home ownership, delinquency history — with window function `RANK()` to identify highest-risk borrower segment per grade
- **Time trends**: Monthly originations, 3-month rolling default rate, vintage cohort analysis with `LAG()` for year-over-year change

---

## Key Findings (Synthetic Data)

- **Grade is the strongest predictor:** Default rates range from ~6% (Grade A) to ~40% (Grade G)
- **Small business loans are highest risk:** ~26% default rate vs ~10% for home improvement loans
- **Income strongly predicts default:** <$40k income borrowers default at ~22% vs ~12% for >$100k
- **Interest rate adverse selection:** Loans >24% carry default rates ~4x those of sub-8% loans
- **Portfolio default rate of ~17%** exceeds the 15% target, driven by Grade D–G and small business

---

## Deploy to Streamlit Community Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file path: `dashboard/app.py`
5. Click Deploy — done

The app auto-generates the database on first launch using synthetic data.

---

## LinkedIn Featured Section

Upload these three items:

1. **PDF Report** — `Consumer_Credit_Risk_Analysis_Abhishek_Dharwadkar.pdf`
   *"Analysed 250,000+ consumer loans using SQL and Python to identify default patterns and high-risk customer segments for credit risk management"*

2. **Dashboard screenshot** — take a screenshot of the running Streamlit dashboard
   *"Interactive Streamlit dashboard tracking consumer credit portfolio performance and risk trends by loan and borrower characteristics"*

3. **This GitHub repository**
   *"SQL and Python code for end-to-end consumer credit risk analysis — portfolio segmentation, default rate modelling, and interactive visualisation"*

---

## Contact

**Abhishek Dharwadkar**
[LinkedIn](https://linkedin.com/in/yourprofile) · [GitHub](https://github.com/yourusername)
