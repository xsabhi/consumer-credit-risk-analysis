"""
Consumer Credit Portfolio Risk Analysis – Streamlit Dashboard
=============================================================
Author  : Abhishek Dharwadkar
Dataset : Lending Club public consumer loan data (or synthetic equivalent)

Run locally:
    streamlit run dashboard/app.py

Deploy:
    Push to GitHub → connect to Streamlit Community Cloud → done.
"""

import sys
from pathlib import Path
import sqlite3

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ── Path resolution so imports work whether run from root or dashboard/ dir ──
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DB_PATH, RISK_LOW_THRESHOLD, RISK_HIGH_THRESHOLD
from src import analysis

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Consumer Credit Risk Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── KPI cards ────────────────────────────────────────────────── */
.kpi-card {
    background: #F0F4F8;
    border-left: 4px solid #1B4F8A;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.kpi-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #5A6A7A;
    margin-bottom: 4px;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1B4F8A;
    line-height: 1.2;
}
.kpi-delta {
    font-size: 0.75rem;
    color: #8A9BAD;
    margin-top: 2px;
}
/* ── Risk colour badges ──────────────────────────────────────── */
.risk-low    { color: #2A9D8F; font-weight: 600; }
.risk-medium { color: #E9C46A; font-weight: 600; }
.risk-high   { color: #E63946; font-weight: 600; }
/* ── Section headers ─────────────────────────────────────────── */
.section-header {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1B4F8A;
    border-bottom: 2px solid #1B4F8A;
    padding-bottom: 4px;
    margin: 16px 0 12px 0;
}
/* ── Sidebar ─────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #1A2E44;
}
section[data-testid="stSidebar"] * {
    color: #D0E4F0 !important;
}
/* ── Footer note ─────────────────────────────────────────────── */
.footer-note {
    font-size: 0.72rem;
    color: #9AABB8;
    text-align: center;
    margin-top: 24px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
GRADE_ORDER   = ["A", "B", "C", "D", "E", "F", "G"]
PURPOSE_ORDER = [
    "debt_consolidation", "credit_card", "home_improvement", "other",
    "major_purchase", "medical", "small_business", "car", "vacation",
    "moving", "house", "wedding", "educational",
]
COLOUR_SCALE_RISK = [
    [0.0, "#2A9D8F"], [0.4, "#E9C46A"], [0.7, "#F4A261"], [1.0, "#E63946"]
]
PRIMARY_BLUE = "#1B4F8A"
ACCENT_RED   = "#E63946"
ACCENT_GREEN = "#2A9D8F"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def ensure_db() -> bool:
    """Check DB exists; if not, build it on-the-fly."""
    if not DB_PATH.exists():
        with st.spinner("⚙️  Building database from synthetic data (first run only)…"):
            from src.data_loader import build_database
            build_database()
    return DB_PATH.exists()


def risk_colour(rate: float) -> str:
    if rate < RISK_LOW_THRESHOLD * 100:
        return ACCENT_GREEN
    elif rate < RISK_HIGH_THRESHOLD * 100:
        return "#E9C46A"
    return ACCENT_RED


def fmt_currency(val: float) -> str:
    if val >= 1_000_000_000:
        return f"${val/1_000_000_000:.1f}B"
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:.0f}"


def fmt_rate(val: float) -> str:
    return f"{val:.2f}%"


@st.cache_data(ttl=300)
def cached_kpis(grades, year_range, purposes):
    return analysis.portfolio_kpis(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_grade(grades, year_range, purposes):
    return analysis.loans_by_grade(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_purpose(grades, year_range, purposes):
    return analysis.loans_by_purpose(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_status(grades, year_range, purposes):
    return analysis.loans_by_status(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_loan_bucket(grades, year_range, purposes):
    return analysis.default_by_loan_amount_bucket(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_int_bucket(grades, year_range, purposes):
    return analysis.default_by_int_rate_bucket(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_income(grades, year_range, purposes):
    return analysis.default_by_income_bracket(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_emp(grades, year_range, purposes):
    return analysis.default_by_emp_length(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_heatmap_gp(grades, year_range, purposes):
    return analysis.heatmap_grade_purpose(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_heatmap_il(grades, year_range, purposes):
    return analysis.heatmap_income_loan_bucket(list(grades), year_range, list(purposes))

@st.cache_data(ttl=300)
def cached_monthly():
    return analysis.monthly_originations()

@st.cache_data(ttl=300)
def cached_vintage():
    return analysis.vintage_default_rates()

@st.cache_data(ttl=300)
def cached_state():
    return analysis.default_by_state()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not ensure_db():
        st.error("❌ Could not initialise database. Please run `python scripts/setup.py` first.")
        st.stop()

    # ── SIDEBAR ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🏦 Credit Risk Dashboard")
        st.markdown("**Consumer Loan Portfolio Analysis**")
        st.markdown("---")

        st.markdown("### Filters")

        sel_grades = tuple(st.multiselect(
            "Credit Grade", options=GRADE_ORDER, default=GRADE_ORDER,
            help="Lending Club credit grades A (lowest risk) to G (highest risk)",
        ))

        sel_years = st.slider(
            "Origination Year", min_value=2014, max_value=2020,
            value=(2014, 2020),
        )

        sel_purposes = tuple(st.multiselect(
            "Loan Purpose", options=PURPOSE_ORDER, default=PURPOSE_ORDER,
        ))

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "Portfolio risk analysis of consumer loans using SQL + Python. "
            "Built to demonstrate credit analytics capability for finance roles."
        )
        st.markdown("**Author:** Abhishek Dharwadkar")
        st.markdown("**Dataset:** Lending Club Public Data")
        st.markdown("**Tools:** Python · SQLite · Streamlit · Plotly")

    # Guard: no grade selected
    if not sel_grades or not sel_purposes:
        st.warning("Please select at least one Grade and one Purpose in the sidebar.")
        st.stop()

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.title("Consumer Credit Portfolio Risk Analysis")
    st.markdown(
        "Interactive risk dashboard analysing consumer loan performance across "
        "credit grades, borrower segments, and origination vintages."
    )

    # ── LOAD DATA ─────────────────────────────────────────────────────────────
    kpis     = cached_kpis(sel_grades, sel_years, sel_purposes)
    df_grade = cached_grade(sel_grades, sel_years, sel_purposes)

    # ── TOP KPI ROW ───────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    total_loans  = int(kpis.get("total_loans", 0))
    total_vol    = float(kpis.get("total_volume", 0) or 0)
    default_rate = float(kpis.get("default_rate_pct", 0) or 0)
    avg_size     = float(kpis.get("avg_loan_size", 0) or 0)
    avg_rate     = float(kpis.get("avg_int_rate", 0) or 0)

    def kpi_card(col, label, value, note=""):
        col.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-delta">{note}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    kpi_card(k1, "Total Loans",       f"{total_loans:,}")
    kpi_card(k2, "Total Volume",       fmt_currency(total_vol))
    kpi_card(k3, "Default Rate",       fmt_rate(default_rate),
             note=f"{'⚠️ Above target' if default_rate > 15 else '✅ Within target'}")
    kpi_card(k4, "Avg Loan Size",      fmt_currency(avg_size))
    kpi_card(k5, "Avg Interest Rate",  fmt_rate(avg_rate))

    st.markdown("---")

    # ── TABS ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Portfolio Overview",
        "⚠️ Default Analysis",
        "🔥 Risk Heatmaps",
        "📈 Vintage Trends",
        "🔍 SQL Explorer",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: PORTFOLIO OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown('<div class="section-header">Portfolio Composition</div>',
                    unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        # Loan volume by grade
        with col_a:
            if not df_grade.empty:
                fig = px.bar(
                    df_grade, x="grade", y="total_volume",
                    color="default_rate",
                    color_continuous_scale=COLOUR_SCALE_RISK,
                    range_color=[0, 40],
                    labels={"grade": "Credit Grade", "total_volume": "Total Volume ($)",
                            "default_rate": "Default Rate (%)"},
                    title="Loan Volume by Credit Grade",
                )
                fig.update_layout(
                    coloraxis_colorbar_title="Default %",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_color="#1A1A2E",
                    title_font_size=14,
                )
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)

        # Loan status donut
        with col_b:
            df_status = cached_status(sel_grades, sel_years, sel_purposes)
            if not df_status.empty:
                STATUS_COLOURS = {
                    "Fully Paid":         ACCENT_GREEN,
                    "Current":            "#4DB8B0",
                    "Charged Off":        ACCENT_RED,
                    "Default":            "#C0392B",
                    "Late (31-120 days)": "#F4A261",
                }
                colours = [STATUS_COLOURS.get(s, "#999") for s in df_status["loan_status"]]
                fig2 = go.Figure(go.Pie(
                    labels=df_status["loan_status"],
                    values=df_status["loan_count"],
                    hole=0.45,
                    marker_colors=colours,
                    textinfo="percent+label",
                    textfont_size=11,
                ))
                fig2.update_layout(
                    title="Loan Status Breakdown",
                    title_font_size=14,
                    showlegend=False,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                )
                st.plotly_chart(fig2, use_container_width=True)

        # Loan count by purpose
        st.markdown('<div class="section-header">Origination Volume by Purpose</div>',
                    unsafe_allow_html=True)
        df_purpose = cached_purpose(sel_grades, sel_years, sel_purposes)
        if not df_purpose.empty:
            df_p_sorted = df_purpose.sort_values("loan_count", ascending=True)
            fig3 = px.bar(
                df_p_sorted, x="loan_count", y="purpose",
                orientation="h",
                color="default_rate",
                color_continuous_scale=COLOUR_SCALE_RISK,
                range_color=[0, 40],
                labels={"loan_count": "Number of Loans", "purpose": "Loan Purpose",
                        "default_rate": "Default Rate (%)"},
                title="Loan Count and Default Rate by Purpose",
            )
            fig3.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font_color="#1A1A2E", title_font_size=14, height=380,
                coloraxis_colorbar_title="Default %",
            )
            st.plotly_chart(fig3, use_container_width=True)

        # Grade table
        st.markdown('<div class="section-header">Grade-level Summary Table</div>',
                    unsafe_allow_html=True)
        if not df_grade.empty:
            display_df = df_grade.copy()
            display_df["total_volume"] = display_df["total_volume"].apply(fmt_currency)
            display_df["default_rate"] = display_df["default_rate"].apply(fmt_rate)
            display_df.columns = ["Grade", "Loan Count", "Total Volume", "Default Rate"]
            st.dataframe(display_df.set_index("Grade"), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: DEFAULT ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown('<div class="section-header">Default Rate by Loan Characteristics</div>',
                    unsafe_allow_html=True)

        col_c, col_d = st.columns(2)

        # Default by loan amount bucket
        with col_c:
            df_lb = cached_loan_bucket(sel_grades, sel_years, sel_purposes)
            if not df_lb.empty:
                bar_colours = [risk_colour(r) for r in df_lb["default_rate"]]
                fig4 = go.Figure(go.Bar(
                    x=df_lb["loan_amnt_bucket"], y=df_lb["default_rate"],
                    marker_color=bar_colours,
                    text=df_lb["default_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                ))
                fig4.update_layout(
                    title="Default Rate by Loan Amount",
                    xaxis_title="Loan Amount", yaxis_title="Default Rate (%)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_color="#1A1A2E", title_font_size=14,
                    yaxis=dict(range=[0, df_lb["default_rate"].max() * 1.25]),
                )
                st.plotly_chart(fig4, use_container_width=True)

        # Default by interest rate bucket
        with col_d:
            df_ib = cached_int_bucket(sel_grades, sel_years, sel_purposes)
            if not df_ib.empty:
                bar_colours2 = [risk_colour(r) for r in df_ib["default_rate"]]
                fig5 = go.Figure(go.Bar(
                    x=df_ib["int_rate_bucket"], y=df_ib["default_rate"],
                    marker_color=bar_colours2,
                    text=df_ib["default_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                ))
                fig5.update_layout(
                    title="Default Rate by Interest Rate",
                    xaxis_title="Interest Rate Band", yaxis_title="Default Rate (%)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_color="#1A1A2E", title_font_size=14,
                    yaxis=dict(range=[0, df_ib["default_rate"].max() * 1.25]),
                )
                st.plotly_chart(fig5, use_container_width=True)

        st.markdown('<div class="section-header">Default Rate by Borrower Characteristics</div>',
                    unsafe_allow_html=True)

        col_e, col_f = st.columns(2)

        # Default by income bracket
        with col_e:
            df_inc = cached_income(sel_grades, sel_years, sel_purposes)
            if not df_inc.empty:
                bar_colours3 = [risk_colour(r) for r in df_inc["default_rate"]]
                fig6 = go.Figure(go.Bar(
                    x=df_inc["income_bracket"], y=df_inc["default_rate"],
                    marker_color=bar_colours3,
                    text=df_inc["default_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                ))
                fig6.update_layout(
                    title="Default Rate by Annual Income",
                    xaxis_title="Income Bracket", yaxis_title="Default Rate (%)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_color="#1A1A2E", title_font_size=14,
                    yaxis=dict(range=[0, df_inc["default_rate"].max() * 1.25]),
                )
                st.plotly_chart(fig6, use_container_width=True)

        # Default by employment length
        with col_f:
            df_emp = cached_emp(sel_grades, sel_years, sel_purposes)
            if not df_emp.empty:
                bar_colours4 = [risk_colour(r) for r in df_emp["default_rate"]]
                fig7 = go.Figure(go.Bar(
                    x=df_emp["emp_length"], y=df_emp["default_rate"],
                    marker_color=bar_colours4,
                    text=df_emp["default_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                ))
                fig7.update_layout(
                    title="Default Rate by Employment Length",
                    xaxis_title="Employment Length", yaxis_title="Default Rate (%)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_color="#1A1A2E", title_font_size=14,
                    yaxis=dict(range=[0, df_emp["default_rate"].max() * 1.25]),
                )
                st.plotly_chart(fig7, use_container_width=True)

        # Purpose default rate ranked
        st.markdown('<div class="section-header">Default Rate Ranking by Loan Purpose</div>',
                    unsafe_allow_html=True)
        df_pur2 = cached_purpose(sel_grades, sel_years, sel_purposes)
        if not df_pur2.empty:
            df_pur_sorted = df_pur2.sort_values("default_rate", ascending=True)
            bar_colours5 = [risk_colour(r) for r in df_pur_sorted["default_rate"]]
            fig8 = go.Figure(go.Bar(
                x=df_pur_sorted["default_rate"],
                y=df_pur_sorted["purpose"],
                orientation="h",
                marker_color=bar_colours5,
                text=df_pur_sorted["default_rate"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside",
            ))
            fig8.update_layout(
                title="Default Rate by Loan Purpose (ranked)",
                xaxis_title="Default Rate (%)", yaxis_title="",
                plot_bgcolor="white", paper_bgcolor="white",
                font_color="#1A1A2E", title_font_size=14, height=420,
                xaxis=dict(range=[0, df_pur_sorted["default_rate"].max() * 1.2]),
            )
            st.plotly_chart(fig8, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: RISK HEATMAPS
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown('<div class="section-header">Default Rate Heatmaps</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "Heatmaps reveal high-risk borrower × loan combinations at a glance. "
            "Darker red = higher default rate."
        )

        col_g, col_h = st.columns(2)

        # Grade × Purpose heatmap
        with col_g:
            df_hm1 = cached_heatmap_gp(sel_grades, sel_years, sel_purposes)
            if not df_hm1.empty:
                fig9 = px.imshow(
                    df_hm1,
                    color_continuous_scale="RdYlGn_r",
                    aspect="auto",
                    labels=dict(x="Credit Grade", y="Loan Purpose", color="Default Rate (%)"),
                    title="Default Rate: Credit Grade × Loan Purpose",
                )
                fig9.update_layout(
                    title_font_size=13, font_color="#1A1A2E",
                    plot_bgcolor="white", paper_bgcolor="white",
                )
                fig9.update_traces(text=df_hm1.values.round(1).astype(str) + "%",
                                   texttemplate="%{text}", textfont_size=9)
                st.plotly_chart(fig9, use_container_width=True)

        # Income × Loan Amount heatmap
        with col_h:
            df_hm2 = cached_heatmap_il(sel_grades, sel_years, sel_purposes)
            if not df_hm2.empty:
                fig10 = px.imshow(
                    df_hm2,
                    color_continuous_scale="RdYlGn_r",
                    aspect="auto",
                    labels=dict(x="Loan Amount", y="Annual Income", color="Default Rate (%)"),
                    title="Default Rate: Income × Loan Amount",
                )
                fig10.update_layout(
                    title_font_size=13, font_color="#1A1A2E",
                    plot_bgcolor="white", paper_bgcolor="white",
                )
                fig10.update_traces(text=df_hm2.values.round(1).astype(str) + "%",
                                    texttemplate="%{text}", textfont_size=10)
                st.plotly_chart(fig10, use_container_width=True)

        # State-level choropleth
        st.markdown('<div class="section-header">Default Rate by U.S. State</div>',
                    unsafe_allow_html=True)
        df_state = cached_state()
        if not df_state.empty:
            fig11 = px.choropleth(
                df_state,
                locations="addr_state",
                locationmode="USA-states",
                color="default_rate",
                color_continuous_scale="RdYlGn_r",
                range_color=[df_state["default_rate"].min(), df_state["default_rate"].max()],
                scope="usa",
                labels={"default_rate": "Default Rate (%)", "addr_state": "State"},
                title="Consumer Loan Default Rate by State",
                hover_data={"loan_count": True},
            )
            fig11.update_layout(
                title_font_size=14, font_color="#1A1A2E",
                paper_bgcolor="white", geo_bgcolor="white",
            )
            st.plotly_chart(fig11, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: VINTAGE TRENDS
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown('<div class="section-header">Portfolio Trends Over Time</div>',
                    unsafe_allow_html=True)

        df_monthly  = cached_monthly()
        df_vintage  = cached_vintage()

        if not df_monthly.empty:
            # Monthly origination volume
            fig12 = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Monthly Loan Originations ($)", "Monthly Default Rate (%)"),
                vertical_spacing=0.12,
                shared_xaxes=True,
            )
            fig12.add_trace(
                go.Bar(x=df_monthly["issue_year_month"],
                       y=df_monthly["total_volume"],
                       name="Volume", marker_color=PRIMARY_BLUE,
                       opacity=0.85),
                row=1, col=1,
            )
            fig12.add_trace(
                go.Scatter(x=df_monthly["issue_year_month"],
                           y=df_monthly["default_rate"],
                           name="Default Rate", line=dict(color=ACCENT_RED, width=2),
                           mode="lines"),
                row=2, col=1,
            )
            fig12.update_layout(
                height=520, showlegend=False,
                plot_bgcolor="white", paper_bgcolor="white",
                font_color="#1A1A2E",
            )
            fig12.update_xaxes(tickangle=45)
            st.plotly_chart(fig12, use_container_width=True)

        if not df_vintage.empty:
            st.markdown('<div class="section-header">Vintage Default Rate Analysis</div>',
                        unsafe_allow_html=True)
            col_i, col_j = st.columns(2)

            with col_i:
                bar_col = [risk_colour(r) for r in df_vintage["default_rate"]]
                fig13 = go.Figure(go.Bar(
                    x=df_vintage["vintage"].astype(str),
                    y=df_vintage["default_rate"],
                    marker_color=bar_col,
                    text=df_vintage["default_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                ))
                fig13.update_layout(
                    title="Default Rate by Origination Vintage",
                    xaxis_title="Vintage Year", yaxis_title="Default Rate (%)",
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_color="#1A1A2E", title_font_size=14,
                    yaxis=dict(range=[0, df_vintage["default_rate"].max() * 1.3]),
                )
                st.plotly_chart(fig13, use_container_width=True)

            with col_j:
                fig14 = go.Figure()
                fig14.add_trace(go.Bar(
                    x=df_vintage["vintage"].astype(str),
                    y=df_vintage["loan_count"],
                    name="Loan Count", marker_color=PRIMARY_BLUE, opacity=0.8,
                    yaxis="y",
                ))
                fig14.add_trace(go.Scatter(
                    x=df_vintage["vintage"].astype(str),
                    y=df_vintage["avg_int_rate"],
                    name="Avg Interest Rate (%)", line=dict(color=ACCENT_RED, width=2),
                    mode="lines+markers", yaxis="y2",
                ))
                fig14.update_layout(
                    title="Origination Volume & Avg Rate by Vintage",
                    xaxis_title="Vintage Year",
                    yaxis=dict(title=dict(text="Loan Count", font=dict(color=PRIMARY_BLUE))),
                    yaxis2=dict(title=dict(text="Avg Interest Rate (%)", font=dict(color=ACCENT_RED)),
                                overlaying="y", side="right"),
                    legend=dict(x=0.01, y=0.99),
                    plot_bgcolor="white", paper_bgcolor="white",
                    font_color="#1A1A2E", title_font_size=14,
                )
                st.plotly_chart(fig14, use_container_width=True)

            # Vintage table
            st.markdown("**Vintage Summary**")
            vt = df_vintage.copy()
            vt["avg_loan_amnt"] = vt["avg_loan_amnt"].apply(fmt_currency)
            vt["default_rate"]  = vt["default_rate"].apply(fmt_rate)
            vt["avg_int_rate"]  = vt["avg_int_rate"].apply(lambda x: f"{x:.2f}%")
            vt.columns = ["Vintage", "Loans Originated", "Default Rate",
                          "Avg Int Rate", "Avg Loan Size"]
            st.dataframe(vt.set_index("Vintage"), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5: SQL EXPLORER
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown('<div class="section-header">Interactive SQL Explorer</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "Run any SQL query directly against the credit portfolio database. "
            "The `loans` table contains all columns from the Lending Club dataset."
        )

        # Sample query presets
        preset = st.selectbox("Load a sample query:", [
            "— Select a preset —",
            "Portfolio KPIs",
            "Default rate by grade",
            "High-risk segments (grade × purpose)",
            "Vintage default rates with YoY change",
            "Top 10 states by default rate",
        ])

        PRESETS = {
            "Portfolio KPIs": (
                "SELECT\n"
                "    COUNT(*)                              AS total_loans,\n"
                "    ROUND(SUM(loan_amnt)/1e6, 1)          AS total_volume_m,\n"
                "    ROUND(AVG(loan_amnt), 0)              AS avg_loan_size,\n"
                "    ROUND(100.0*SUM(is_default)/COUNT(*),2) AS default_rate_pct\n"
                "FROM loans;"
            ),
            "Default rate by grade": (
                "SELECT grade,\n"
                "       COUNT(*) AS loan_count,\n"
                "       ROUND(100.0*SUM(is_default)/COUNT(*),2) AS default_rate_pct\n"
                "FROM loans\n"
                "GROUP BY grade\n"
                "ORDER BY grade;"
            ),
            "High-risk segments (grade × purpose)": (
                "WITH seg AS (\n"
                "  SELECT grade, purpose,\n"
                "         COUNT(*) AS n,\n"
                "         ROUND(100.0*SUM(is_default)/COUNT(*),2) AS dr\n"
                "  FROM loans\n"
                "  GROUP BY grade, purpose\n"
                "  HAVING n >= 100\n"
                ")\n"
                "SELECT * FROM seg WHERE dr >= 25 ORDER BY dr DESC LIMIT 15;"
            ),
            "Vintage default rates with YoY change": (
                "SELECT issue_year AS vintage,\n"
                "       COUNT(*) AS loans,\n"
                "       ROUND(100.0*SUM(is_default)/COUNT(*),2) AS default_rate_pct,\n"
                "       ROUND(\n"
                "         ROUND(100.0*SUM(is_default)/COUNT(*),2)\n"
                "         - LAG(ROUND(100.0*SUM(is_default)/COUNT(*),2))\n"
                "           OVER (ORDER BY issue_year), 2\n"
                "       ) AS yoy_change\n"
                "FROM loans\n"
                "WHERE issue_year IS NOT NULL\n"
                "GROUP BY issue_year\n"
                "ORDER BY issue_year;"
            ),
            "Top 10 states by default rate": (
                "SELECT addr_state AS state,\n"
                "       COUNT(*) AS loan_count,\n"
                "       ROUND(100.0*SUM(is_default)/COUNT(*),2) AS default_rate_pct\n"
                "FROM loans\n"
                "GROUP BY addr_state\n"
                "HAVING loan_count >= 500\n"
                "ORDER BY default_rate_pct DESC\n"
                "LIMIT 10;"
            ),
        }

        default_sql = PRESETS.get(preset, "SELECT * FROM loans LIMIT 10;")

        # When a preset is chosen, push it into session state so the text area updates
        if preset != "— Select a preset —":
            st.session_state["sql_editor"] = default_sql

        sql_input = st.text_area("SQL Query", value=default_sql, height=160,
                                key="sql_editor")

        if st.button("▶ Run Query", type="primary"):
            try:
                from src.database import query as run_query
                result = run_query(sql_input)
                st.success(f"Returned {len(result):,} rows.")
                st.dataframe(result, use_container_width=True)
            except Exception as exc:
                st.error(f"Query error: {exc}")

        st.markdown("**Available columns:** `loan_id`, `loan_amnt`, `funded_amnt`, "
                    "`term`, `int_rate`, `installment`, `grade`, `sub_grade`, "
                    "`emp_length`, `home_ownership`, `annual_inc`, `loan_status`, "
                    "`purpose`, `dti`, `delinq_2yrs`, `fico_range_low`, "
                    "`fico_range_high`, `issue_d`, `addr_state`, `open_acc`, "
                    "`pub_rec`, `revol_bal`, `revol_util`, `total_acc`, "
                    "`is_default`, `loan_amnt_bucket`, `income_bracket`, "
                    "`int_rate_bucket`, `issue_year`, `issue_month`, "
                    "`issue_year_month`, `fico_mid`, `lti`")

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="footer-note">Consumer Credit Portfolio Risk Analysis · '
        'Abhishek Dharwadkar · Built with Python, SQLite, Streamlit & Plotly</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
