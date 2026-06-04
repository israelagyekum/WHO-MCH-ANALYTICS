"""
MCH Policy Intelligence Dashboard
Maternal & Child Health — WHO Data | Ministry of Health, Ghana
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

# ── Absolute path fix (works locally AND on Streamlit Cloud) ──────────────────
ROOT      = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT, "data", "processed", "mch_panel_data.csv")
sys.path.insert(0, ROOT)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.inspection import partial_dependence
import statsmodels.formula.api as smf
import statsmodels.api as sm

# ── WHO Official Colour Palette ───────────────────────────────────────────────
WHO_NAVY   = "#003F87"
WHO_BLUE   = "#009FD4"
WHO_GREEN  = "#00A651"
WHO_RED    = "#E63329"
WHO_AMBER  = "#F39200"
WHO_GRAY   = "#6D6E71"
WHO_LIGHT  = "#EFF6FB"
WHO_WHITE  = "#FFFFFF"

COLOR_SEQ  = [WHO_NAVY, WHO_BLUE, WHO_GREEN, WHO_AMBER, WHO_RED,
              "#5C6BC0", "#AB47BC", "#26C6DA"]

FEATURES = [
    "gdp_per_capita",
    "fertility_rate",
    "health_expenditure_per_capita",
    "female_secondary_enrollment",
]
FEATURE_LABELS = {
    "gdp_per_capita":                "GDP per Capita (USD)",
    "fertility_rate":                "Fertility Rate",
    "health_expenditure_per_capita": "Health Expenditure per Capita (USD)",
    "female_secondary_enrollment":   "Female Secondary Enrollment (%)",
}
TARGET = "maternal_mortality"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCH Policy Dashboard — Ghana MoH",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{
    background-color: #F4F7FB;
  }}
  [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {WHO_NAVY} 0%, #002966 100%);
    padding-top: 1rem;
  }}
  [data-testid="stSidebar"] * {{ color: {WHO_WHITE} !important; }}
  [data-testid="stSidebar"] .stSelectbox > div > div,
  [data-testid="stSidebar"] .stRadio > div {{
    background: rgba(255,255,255,0.08) !important;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.2) !important;
  }}
  h1, h2, h3, h4 {{
    color: {WHO_NAVY} !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
  }}
  [data-testid="metric-container"] {{
    background: {WHO_WHITE};
    border: 1px solid #D6E8F7;
    border-left: 5px solid {WHO_BLUE};
    border-radius: 8px;
    padding: 0.75rem 1rem;
    box-shadow: 0 2px 8px rgba(0,63,135,0.07);
  }}
  [data-testid="stMetricValue"] {{
    color: {WHO_NAVY} !important;
    font-weight: 700;
    font-size: 1.5rem !important;
  }}
  [data-testid="stMetricLabel"] {{
    color: {WHO_GRAY} !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {WHO_LIGHT};
    border-radius: 10px 10px 0 0;
    padding: 6px 6px 0;
  }}
  .stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {WHO_GRAY};
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 8px 18px;
    border: none;
  }}
  .stTabs [aria-selected="true"] {{
    background: {WHO_NAVY} !important;
    color: {WHO_WHITE} !important;
  }}
  .sec-hdr {{
    background: linear-gradient(90deg, {WHO_NAVY}, {WHO_BLUE});
    color: white;
    padding: 0.45rem 1rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.95rem;
    margin: 1.2rem 0 0.8rem;
    letter-spacing: 0.02em;
  }}
  [data-testid="stInfo"] {{
    background: {WHO_LIGHT};
    border-left: 4px solid {WHO_BLUE};
  }}
  footer, #MainMenu {{ display: none !important; visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ── WHO Masthead ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,{WHO_NAVY} 0%,{WHO_BLUE} 100%);
            padding:1.4rem 2rem;border-radius:12px;margin-bottom:1.2rem;
            box-shadow:0 4px 20px rgba(0,63,135,0.25);">
  <div style="color:white;font-size:1.65rem;font-weight:800;
              font-family:'Segoe UI',Arial,sans-serif;line-height:1.2;">
    🏥 &nbsp;MCH Policy Intelligence Dashboard
  </div>
  <div style="color:rgba(255,255,255,0.82);font-size:0.9rem;margin-top:0.35rem;">
    Maternal &amp; Child Health &nbsp;·&nbsp; WHO / World Bank Data &nbsp;·&nbsp;
    Ministry of Health, Ghana &nbsp;·&nbsp;
    Explainable AI &nbsp;·&nbsp; Panel Econometrics &nbsp;·&nbsp; Policy Simulation
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA & MODELS  —  all in-memory, no pkl (version-safe for Streamlit Cloud)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=FEATURES + [TARGET])
    df["log_mmr"]        = np.log(df[TARGET].clip(lower=1))
    df["log_gdp"]        = np.log(df["gdp_per_capita"].clip(lower=1))
    df["log_health_exp"] = np.log(df["health_expenditure_per_capita"].clip(lower=1))
    return df


@st.cache_resource(show_spinner=False)
def train_models(_n):
    df   = load_data()
    X, y = df[FEATURES], df[TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestRegressor(
        n_estimators=150, max_depth=8, min_samples_leaf=3,
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_tr, y_tr); rf_p = rf.predict(X_te)

    gb = GradientBoostingRegressor(
        n_estimators=150, learning_rate=0.08, max_depth=4,
        subsample=0.8, random_state=42,
    )
    gb.fit(X_tr, y_tr); gb_p = gb.predict(X_te)

    def met(yt, yp):
        return {"r2": r2_score(yt, yp),
                "rmse": float(np.sqrt(mean_squared_error(yt, yp))),
                "mae":  mean_absolute_error(yt, yp)}

    return dict(rf=rf, gb=gb,
                X_train=X_tr, X_test=X_te, y_train=y_tr, y_test=y_te,
                rf_metrics=met(y_te, rf_p), gb_metrics=met(y_te, gb_p))


@st.cache_data(show_spinner=False)
def run_econometrics(_n):
    df = load_data()
    X_ols = sm.add_constant(df[["log_gdp","log_health_exp",
                                 "fertility_rate","female_secondary_enrollment"]])
    ols = sm.OLS(df["log_mmr"], X_ols).fit(cov_type="HC3")
    fe  = smf.ols(
        "log_mmr ~ log_gdp + log_health_exp + fertility_rate"
        " + female_secondary_enrollment + C(country) + C(year)",
        data=df,
    ).fit(cov_type="cluster", cov_kwds={"groups": df["country"]})
    return ols, fe


# ── Bootstrap ─────────────────────────────────────────────────────────────────
with st.spinner("Loading WHO dataset and initialising models…"):
    df     = load_data()
    models = train_models(len(df))

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 Dashboard Controls")
    st.markdown("---")
    all_countries = sorted(df["country"].unique())
    default_idx   = all_countries.index("Ghana") if "Ghana" in all_countries else 0
    country = st.selectbox("📍 Country", all_countries, index=default_idx)

    all_years = sorted(df["year"].unique())
    year = st.selectbox("📅 Reference Year", all_years, index=len(all_years) - 1)

    st.markdown("---")
    model_choice = st.radio("🤖 Active ML Model",
                            ["Random Forest", "Gradient Boosting"])
    st.markdown("---")
    st.markdown(
        f"<div style='font-size:0.8rem;line-height:1.9;'>"
        f"<b>Data:</b> WHO / World Bank<br>"
        f"<b>Countries:</b> {df['country'].nunique()}<br>"
        f"<b>Period:</b> {df['year'].min()}–{df['year'].max()}<br>"
        f"<b>Observations:</b> {len(df):,}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.72rem;color:rgba(255,255,255,0.5);text-align:center;'>"
        "Ministry of Health, Ghana<br>MPhil Data Science · 2026</div>",
        unsafe_allow_html=True)

# ── Derived ────────────────────────────────────────────────────────────────────
active_model   = models["rf"] if model_choice == "Random Forest" else models["gb"]
active_metrics = models["rf_metrics"] if model_choice == "Random Forest" else models["gb_metrics"]
country_df     = df[df["country"] == country]
row_df         = country_df[country_df["year"] == year]
if row_df.empty:
    row_df = country_df.sort_values("year").iloc[[-1]]
row = row_df.iloc[0]

_L = dict(plot_bgcolor=WHO_WHITE, paper_bgcolor=WHO_WHITE,
          font=dict(family="Segoe UI, Arial", size=12, color="#2D3748"),
          title_font=dict(size=13, color=WHO_NAVY, family="Segoe UI, Arial"),
          margin=dict(t=50, b=40, l=40, r=20))

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍  Global Overview",
    "🔬  Country Analysis",
    "📊  Econometric Models",
    "🤖  XAI & Feature Analysis",
    "🎯  Policy Simulation",
])


# ════════════════════════════════════════════════════
# TAB 1 — GLOBAL OVERVIEW
# ════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="sec-hdr">🌍 Global Maternal Mortality Overview</div>',
                unsafe_allow_html=True)

    latest = df.sort_values("year").groupby("country", as_index=False).last()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Countries Tracked",       f"{df['country'].nunique()}")
    k2.metric("Global Avg MMR",          f"{latest[TARGET].mean():.0f}",
              help="per 100,000 live births")
    k3.metric("Avg Health Expenditure",  f"${latest['health_expenditure_per_capita'].mean():.0f}",
              help="per capita USD")
    k4.metric("Avg Fertility Rate",      f"{latest['fertility_rate'].mean():.2f}")
    k5.metric("Avg Female Education",    f"{latest['female_secondary_enrollment'].mean():.1f}%")

    st.markdown("---")
    cm, ct = st.columns([3, 2])

    with cm:
        fig_map = px.choropleth(
            latest, locations="country", locationmode="country names",
            color=TARGET,
            title="Maternal Mortality Rate — Latest Available Year",
            color_continuous_scale=["#EFF6FB", WHO_BLUE, WHO_NAVY, WHO_RED],
            labels={TARGET: "MMR per 100k"},
        )
        fig_map.update_layout(**_L,
            geo=dict(showframe=False, showcoastlines=True,
                     projection_type="natural earth", bgcolor=WHO_WHITE),
            coloraxis_colorbar=dict(title="MMR<br>per 100k",
                                    title_font=dict(size=11)))
        st.plotly_chart(fig_map, use_container_width=True)

    with ct:
        top10 = latest.nlargest(10, TARGET)[["country", TARGET]].reset_index(drop=True)
        fig_top = px.bar(
            top10, x=TARGET, y="country", orientation="h",
            title="Top 10 Highest MMR Countries",
            color=TARGET, color_continuous_scale=[WHO_AMBER, WHO_RED],
            labels={TARGET: "MMR per 100k", "country": ""},
        )
        fig_top.update_layout(**_L, showlegend=False,
                              yaxis=dict(autorange="reversed"),
                              coloraxis_showscale=False)
        st.plotly_chart(fig_top, use_container_width=True)

    global_trend = df.groupby("year")[TARGET].mean().reset_index()
    fig_gt = px.line(
        global_trend, x="year", y=TARGET,
        title="Global Average MMR Trend",
        color_discrete_sequence=[WHO_BLUE],
        labels={TARGET: "MMR per 100k", "year": "Year"},
    )
    fig_gt.update_traces(line_width=3)
    fig_gt.add_scatter(x=global_trend["year"], y=global_trend[TARGET],
                       mode="markers", marker=dict(color=WHO_NAVY, size=6),
                       showlegend=False)
    fig_gt.update_layout(**_L,
        xaxis=dict(gridcolor="#E8EFF8", dtick=2),
        yaxis=dict(gridcolor="#E8EFF8"))
    st.plotly_chart(fig_gt, use_container_width=True)

    st.markdown('<div class="sec-hdr">Key Correlations — All Countries</div>',
                unsafe_allow_html=True)
    fig_sc = px.scatter(
        latest, x="gdp_per_capita", y=TARGET,
        size="health_expenditure_per_capita", color="fertility_rate",
        hover_name="country", log_x=True,
        color_continuous_scale=[WHO_GREEN, WHO_AMBER, WHO_RED],
        title="GDP per Capita vs MMR  (bubble = health spending · colour = fertility)",
        labels={"gdp_per_capita": "GDP per Capita (USD, log scale)",
                TARGET: "MMR per 100k", "fertility_rate": "Fertility Rate"},
    )
    fig_sc.update_layout(**_L)
    st.plotly_chart(fig_sc, use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 2 — COUNTRY ANALYSIS
# ════════════════════════════════════════════════════
with tab2:
    st.markdown(f'<div class="sec-hdr">🔬 Country Deep Dive — {country}</div>',
                unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Maternal Mortality",  f"{row[TARGET]:.0f}",
              help="per 100,000 live births")
    c2.metric("GDP per Capita",      f"${row['gdp_per_capita']:,.0f}")
    c3.metric("Health Expenditure",  f"${row['health_expenditure_per_capita']:,.0f}")
    c4.metric("Fertility Rate",      f"{row['fertility_rate']:.2f}")
    c5.metric("Female Education",    f"{row['female_secondary_enrollment']:.1f}%")

    st.markdown("---")
    ca, cb = st.columns(2)

    with ca:
        fig_a = px.area(
            country_df.sort_values("year"), x="year", y=TARGET,
            title=f"Maternal Mortality Trend — {country}",
            labels={TARGET: "MMR per 100k", "year": "Year"},
            color_discrete_sequence=[WHO_BLUE],
        )
        fig_a.update_traces(
            fillcolor="rgba(0,159,212,0.12)",
            line_color=WHO_BLUE, line_width=2.5)
        fig_a.update_layout(**_L)
        st.plotly_chart(fig_a, use_container_width=True)

    with cb:
        fig_b = px.line(
            country_df.sort_values("year"), x="year",
            y="health_expenditure_per_capita",
            title=f"Health Expenditure Trend — {country}",
            labels={"health_expenditure_per_capita": "USD per capita", "year": "Year"},
            color_discrete_sequence=[WHO_GREEN],
        )
        fig_b.update_traces(line_width=2.5)
        fig_b.update_layout(**_L)
        st.plotly_chart(fig_b, use_container_width=True)

    st.markdown('<div class="sec-hdr">Regional / Peer Comparison</div>',
                unsafe_allow_html=True)
    default_peers = [c for c in
                     ["Ghana","Nigeria","Kenya","Ethiopia","Senegal"]
                     if c in df["country"].unique() and c != country][:3]
    comp_sel = st.multiselect(
        "Countries to compare", all_countries,
        default=[country] + default_peers)

    if comp_sel:
        fig_cp = px.line(
            df[df["country"].isin(comp_sel)].sort_values("year"),
            x="year", y=TARGET, color="country",
            title="MMR Comparison — Selected Countries",
            color_discrete_sequence=COLOR_SEQ,
            labels={TARGET: "MMR per 100k", "year": "Year"},
        )
        for tr in fig_cp.data:
            if tr.name == country:
                tr.line.width = 4
                tr.line.color = WHO_RED
        fig_cp.update_layout(**_L)
        st.plotly_chart(fig_cp, use_container_width=True)

    yr_df = df[df["year"] == year].copy()
    fig_s2 = px.scatter(
        yr_df, x="gdp_per_capita", y=TARGET,
        hover_name="country",
        size="health_expenditure_per_capita", color="fertility_rate",
        log_x=True, color_continuous_scale=[WHO_GREEN, WHO_AMBER, WHO_RED],
        title=f"GDP per Capita vs MMR ({year}) — {country} starred",
        labels={"gdp_per_capita": "GDP per Capita (USD, log scale)",
                TARGET: "MMR per 100k",
                "fertility_rate": "Fertility Rate"},
    )
    if not row_df.empty:
        fig_s2.add_scatter(
            x=[row["gdp_per_capita"]], y=[row[TARGET]],
            mode="markers+text", text=[f"  {country}"],
            textposition="middle right",
            marker=dict(color=WHO_RED, size=16, symbol="star",
                        line=dict(color=WHO_NAVY, width=2)),
            showlegend=False)
    fig_s2.update_layout(**_L)
    st.plotly_chart(fig_s2, use_container_width=True)


# ════════════════════════════════════════════════════
# TAB 3 — ECONOMETRIC MODELS
# ════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec-hdr">📊 Panel Econometric Analysis</div>',
                unsafe_allow_html=True)

    with st.spinner("Running regressions…"):
        ols_m, fe_m = run_econometrics(len(df))

    CVARS  = ["log_gdp","log_health_exp","fertility_rate","female_secondary_enrollment"]
    CLBLS  = ["log(GDP p.c.)","log(Health Exp.)","Fertility Rate","Female Education"]

    col_o, col_f = st.columns(2)

    def sig(p):
        return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""

    with col_o:
        st.markdown("#### Pooled OLS — Log-Log Specification")
        st.caption("Dep. var: ln(MMR)  |  Robust SE (HC3)")
        rows_o = [{"Variable": lbl,
                   "Coef.":    round(ols_m.params[v], 4),
                   "Std Err":  round(ols_m.bse[v], 4),
                   "t":        round(ols_m.tvalues[v], 3),
                   "p":        round(ols_m.pvalues[v], 4),
                   "Sig.":     sig(ols_m.pvalues[v])}
                  for v, lbl in zip(CVARS, CLBLS) if v in ols_m.params.index]
        st.dataframe(pd.DataFrame(rows_o), use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame({
            "Metric": ["R²","Adj. R²","F-stat","N"],
            "Value":  [f"{ols_m.rsquared:.4f}", f"{ols_m.rsquared_adj:.4f}",
                       f"{ols_m.fvalue:.2f}", f"{int(ols_m.nobs):,}"],
        }), use_container_width=True, hide_index=True)
        st.caption("*** p<0.01  ** p<0.05  * p<0.1")

    with col_f:
        st.markdown("#### Two-Way Fixed Effects")
        st.caption("Country FE + Year FE  |  Clustered SE by country")
        rows_f = [{"Variable": lbl,
                   "Coef.":    round(fe_m.params[v], 4),
                   "Std Err":  round(fe_m.bse[v], 4),
                   "t":        round(fe_m.tvalues[v], 3),
                   "p":        round(fe_m.pvalues[v], 4),
                   "Sig.":     sig(fe_m.pvalues[v])}
                  for v, lbl in zip(CVARS, CLBLS) if v in fe_m.params.index]
        st.dataframe(pd.DataFrame(rows_f), use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame({
            "Metric": ["Within R²","F-stat","N","Countries","Years"],
            "Value":  [f"{fe_m.rsquared:.4f}", f"{fe_m.fvalue:.2f}",
                       f"{int(fe_m.nobs):,}", f"{df['country'].nunique()}",
                       f"{df['year'].nunique()}"],
        }), use_container_width=True, hide_index=True)
        st.caption("*** p<0.01  ** p<0.05  * p<0.1")

    st.markdown('<div class="sec-hdr">Coefficient Plot — OLS vs Fixed Effects (95% CI)</div>',
                unsafe_allow_html=True)

    coef_rows = []
    for v, lbl in zip(CVARS, CLBLS):
        for mdl, mname in [(ols_m, "Pooled OLS"), (fe_m, "Fixed Effects")]:
            if v in mdl.params.index:
                ci = mdl.conf_int().loc[v]
                coef_rows.append(dict(Model=mname, Variable=lbl,
                                      Coef=mdl.params[v],
                                      CI_lo=ci[0], CI_hi=ci[1]))

    cdf = pd.DataFrame(coef_rows)
    fig_c = go.Figure()
    for mname, clr in [("Pooled OLS", WHO_BLUE), ("Fixed Effects", WHO_NAVY)]:
        s = cdf[cdf["Model"] == mname]
        fig_c.add_trace(go.Scatter(
            x=s["Variable"], y=s["Coef"],
            error_y=dict(type="data", symmetric=False,
                         array=s["CI_hi"] - s["Coef"],
                         arrayminus=s["Coef"] - s["CI_lo"],
                         thickness=2, width=6),
            mode="markers",
            marker=dict(size=11, color=clr, symbol="circle",
                        line=dict(color=WHO_WHITE, width=1.5)),
            name=mname,
        ))
    fig_c.add_hline(y=0, line_dash="dash", line_color=WHO_GRAY, line_width=1.2)
    fig_c.update_layout(**_L,
        title="Coefficient Estimates with 95% Confidence Intervals",
        xaxis_title="Explanatory Variable",
        yaxis_title="Coefficient on ln(MMR)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_c, use_container_width=True)

    st.markdown('<div class="sec-hdr">Economic Interpretation</div>', unsafe_allow_html=True)
    gdp_o = ols_m.params.get("log_gdp", 0)
    gdp_f = fe_m.params.get("log_gdp", 0)
    hlt_o = ols_m.params.get("log_health_exp", 0)
    hlt_f = fe_m.params.get("log_health_exp", 0)
    fer_f = fe_m.params.get("fertility_rate", 0)
    edu_f = fe_m.params.get("female_secondary_enrollment", 0)

    st.info(f"""
**Key Findings from the Panel Analysis**

**GDP per Capita** — A 1 % rise in GDP per capita is associated with a
**{abs(gdp_o):.2f} % {'decrease' if gdp_o < 0 else 'increase'}** in MMR (Pooled OLS) and
**{abs(gdp_f):.2f} % {'decrease' if gdp_f < 0 else 'increase'}** after controlling for unobserved country and year effects (Fixed Effects).

**Health Expenditure** — A 1 % increase in health spending per capita is associated with a
**{abs(hlt_o):.2f} % {'decrease' if hlt_o < 0 else 'increase'}** in MMR (OLS) vs
**{abs(hlt_f):.2f} % {'decrease' if hlt_f < 0 else 'increase'}** (FE).

**Fertility Rate** — Each unit rise in fertility is associated with a
**{abs(fer_f):.3f} {'decrease' if fer_f < 0 else 'increase'}** in ln(MMR) under Fixed Effects.

**Female Education** — Each 1 pp increase in female secondary enrolment is associated with a
**{abs(edu_f):.4f} {'decrease' if edu_f < 0 else 'increase'}** in ln(MMR).

> Two-way fixed effects remove unobserved country heterogeneity (governance, geography, culture)
> and global time shocks, yielding cleaner policy-relevant estimates than pooled OLS.
""")


# ════════════════════════════════════════════════════
# TAB 4 — XAI & FEATURE ANALYSIS
# ════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="sec-hdr">🤖 Explainable AI — Model Interpretability</div>',
                unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Model",  model_choice)
    m2.metric("R² (test)",     f"{active_metrics['r2']:.4f}")
    m3.metric("RMSE",          f"{active_metrics['rmse']:.2f}")
    m4.metric("MAE",           f"{active_metrics['mae']:.2f}")

    st.markdown("#### Model Comparison")
    st.dataframe(pd.DataFrame({
        "Model": ["Random Forest", "Gradient Boosting"],
        "R²":    [models["rf_metrics"]["r2"],   models["gb_metrics"]["r2"]],
        "RMSE":  [models["rf_metrics"]["rmse"], models["gb_metrics"]["rmse"]],
        "MAE":   [models["rf_metrics"]["mae"],  models["gb_metrics"]["mae"]],
    }).round(4), use_container_width=True, hide_index=True)

    st.markdown("---")
    cfi, csh = st.columns(2)

    with cfi:
        st.markdown("#### Feature Importance (Gini Impurity)")
        fi_df = pd.DataFrame({
            "Feature":    [FEATURE_LABELS[f] for f in FEATURES],
            "Importance": active_model.feature_importances_,
        }).sort_values("Importance")
        fig_fi = go.Figure(go.Bar(
            x=fi_df["Importance"], y=fi_df["Feature"], orientation="h",
            marker=dict(color=fi_df["Importance"],
                        colorscale=[[0, WHO_LIGHT],[0.5, WHO_BLUE],[1, WHO_NAVY]],
                        showscale=False),
            text=[f"{v:.3f}" for v in fi_df["Importance"]],
            textposition="outside",
        ))
        fig_fi.update_layout(**_L,
            title="Feature Importance", xaxis_title="Importance Score")
        st.plotly_chart(fig_fi, use_container_width=True)

    with csh:
        st.markdown("#### SHAP — Mean Absolute Impact")
        try:
            explainer = shap.TreeExplainer(models["rf"])
            shap_arr  = explainer.shap_values(models["X_test"])
            mean_shap = np.abs(shap_arr).mean(axis=0)

            shap_df = pd.DataFrame({
                "Feature":     [FEATURE_LABELS[f] for f in FEATURES],
                "Mean |SHAP|": mean_shap,
            }).sort_values("Mean |SHAP|")

            fig_sh = go.Figure(go.Bar(
                x=shap_df["Mean |SHAP|"], y=shap_df["Feature"],
                orientation="h", marker_color=WHO_BLUE,
                text=[f"{v:.1f}" for v in shap_df["Mean |SHAP|"]],
                textposition="outside",
            ))
            fig_sh.update_layout(**_L,
                title="Mean |SHAP| — Random Forest",
                xaxis_title="Mean |SHAP Value|")
            st.plotly_chart(fig_sh, use_container_width=True)
        except Exception as e:
            st.warning(f"SHAP error: {e}")

    # SHAP waterfall for selected country
    st.markdown(f'<div class="sec-hdr">SHAP Waterfall — {country} ({year})</div>',
                unsafe_allow_html=True)
    try:
        row_feat = pd.DataFrame([{f: row[f] for f in FEATURES}])
        shap_row = explainer.shap_values(row_feat)[0]

        wf = pd.DataFrame({
            "Feature":       [FEATURE_LABELS[f] for f in FEATURES],
            "SHAP Value":    shap_row,
            "Feature Value": [row[f] for f in FEATURES],
        }).sort_values("SHAP Value")

        fig_wf = go.Figure(go.Bar(
            x=wf["SHAP Value"], y=wf["Feature"], orientation="h",
            marker_color=[WHO_GREEN if v < 0 else WHO_RED for v in wf["SHAP Value"]],
            text=[f"val={v:.2f}" for v in wf["Feature Value"]],
            textposition="outside",
        ))
        fig_wf.add_vline(x=0, line_color=WHO_GRAY, line_dash="dash", line_width=1.2)
        fig_wf.update_layout(**_L,
            title=f"SHAP Contributions to MMR Prediction — {country}",
            xaxis_title="SHAP Value (impact on predicted MMR)")
        st.plotly_chart(fig_wf, use_container_width=True)
        st.caption(
            "🟢 Green = reduces MMR (beneficial)  ·  "
            "🔴 Red = increases MMR (adverse)  ·  "
            f"Baseline E[f(x)] = {explainer.expected_value:.1f}"
        )
    except Exception as e:
        st.warning(f"SHAP waterfall: {e}")

    # PDP
    st.markdown('<div class="sec-hdr">Partial Dependence Plot</div>',
                unsafe_allow_html=True)
    pdp_feat = st.selectbox(
        "Select feature", FEATURES,
        format_func=lambda x: FEATURE_LABELS[x])

    try:
        pdp_r = partial_dependence(
            models["rf"], models["X_test"],
            features=[FEATURES.index(pdp_feat)], grid_resolution=60)
        pdp_df = pd.DataFrame({
            "Feature Value": pdp_r["grid_values"][0],
            "Predicted MMR": pdp_r["average"][0],
        })
        fig_pd = px.line(
            pdp_df, x="Feature Value", y="Predicted MMR",
            title=f"Partial Dependence — {FEATURE_LABELS[pdp_feat]}",
            color_discrete_sequence=[WHO_NAVY],
            labels={"Feature Value": FEATURE_LABELS[pdp_feat]},
        )
        fig_pd.update_traces(line_width=3)
        fig_pd.add_scatter(x=pdp_df["Feature Value"], y=pdp_df["Predicted MMR"],
                           mode="markers", marker=dict(color=WHO_BLUE, size=5),
                           showlegend=False)
        fig_pd.add_vline(x=row[pdp_feat], line_dash="dot",
                         line_color=WHO_RED, line_width=2,
                         annotation_text=f"{country}",
                         annotation_font_color=WHO_RED)
        fig_pd.update_layout(**_L,
            xaxis=dict(gridcolor="#E8EFF8"),
            yaxis=dict(gridcolor="#E8EFF8"))
        st.plotly_chart(fig_pd, use_container_width=True)
        st.caption(f"Red dashed line = current value for {country} ({year})")
    except Exception as e:
        st.warning(f"PDP: {e}")


# ════════════════════════════════════════════════════
# TAB 5 — POLICY SIMULATION
# ════════════════════════════════════════════════════
with tab5:
    st.markdown(f'<div class="sec-hdr">🎯 Policy Simulation — {country} · {year}</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Adjust the policy levers below to project the impact on Maternal Mortality Rate. "
        "Results are generated by the active ML model in real time."
    )

    sl1, sl2 = st.columns(2)
    with sl1:
        gdp_pct    = st.slider("💰 GDP per Capita Change (%)",            -30, 60, 0, step=5)
        health_pct = st.slider("🏥 Health Expenditure Change (%)",         -30, 100, 0, step=5)
    with sl2:
        fert_pct   = st.slider("👶 Fertility Rate Change (%)",             -50, 20, 0, step=5)
        edu_pct    = st.slider("📚 Female Secondary Enrolment Change (%)", -20, 60, 0, step=5)

    scenario_name = st.text_input("📋 Name this scenario", "Policy Scenario A")

    b_vals = {f: row[f] for f in FEATURES}
    s_vals = {
        "gdp_per_capita":                row["gdp_per_capita"]                * (1 + gdp_pct    / 100),
        "fertility_rate":                row["fertility_rate"]                * (1 + fert_pct   / 100),
        "health_expenditure_per_capita": row["health_expenditure_per_capita"] * (1 + health_pct / 100),
        "female_secondary_enrollment":   row["female_secondary_enrollment"]   * (1 + edu_pct    / 100),
    }

    b_pred = active_model.predict(pd.DataFrame([b_vals])[FEATURES])[0]
    s_pred = active_model.predict(pd.DataFrame([s_vals])[FEATURES])[0]
    d_abs  = b_pred - s_pred
    d_pct  = (s_pred - b_pred) / b_pred * 100

    st.markdown("---")
    st.markdown("### Simulation Results")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Baseline MMR",       f"{b_pred:.1f}")
    r2.metric("Projected MMR",      f"{s_pred:.1f}",
              delta=f"{d_pct:+.1f}%", delta_color="inverse")
    r3.metric("MMR Change /100k",   f"{d_abs:+.1f}", delta_color="inverse")
    r4.metric("Outcome",
              "✅ Reduction" if d_abs > 0 else "⚠️ Increase" if d_abs < 0 else "No change",
              delta_color="inverse")

    vz1, vz2 = st.columns(2)

    with vz1:
        bar_clr = WHO_GREEN if s_pred < b_pred else WHO_RED
        fig_sm = go.Figure(go.Bar(
            x=["Baseline", scenario_name], y=[b_pred, s_pred],
            marker_color=[WHO_BLUE, bar_clr],
            text=[f"{b_pred:.1f}", f"{s_pred:.1f}"],
            textposition="outside", width=0.45,
        ))
        fig_sm.add_hline(y=b_pred, line_dash="dot",
                         line_color=WHO_GRAY, line_width=1.5)
        fig_sm.update_layout(**_L,
            title="Baseline vs Policy Scenario",
            yaxis_title="MMR per 100,000 live births",
            yaxis_range=[0, max(b_pred, s_pred) * 1.2])
        st.plotly_chart(fig_sm, use_container_width=True)

    with vz2:
        tornado = []
        for lbl, col, pct in [
            ("💰 GDP",              "gdp_per_capita",                gdp_pct),
            ("🏥 Health Spending",  "health_expenditure_per_capita", health_pct),
            ("👶 Fertility Rate",   "fertility_rate",                fert_pct),
            ("📚 Female Education", "female_secondary_enrollment",   edu_pct),
        ]:
            if pct != 0:
                tmp = pd.DataFrame([b_vals])[FEATURES].copy()
                tmp[col] = row[col] * (1 + pct / 100)
                tornado.append({"Lever": lbl,
                                 "Impact": b_pred - active_model.predict(tmp)[0]})

        if tornado:
            tdf = pd.DataFrame(tornado).sort_values("Impact")
            fig_t = go.Figure(go.Bar(
                x=tdf["Impact"], y=tdf["Lever"], orientation="h",
                marker_color=[WHO_GREEN if v > 0 else WHO_RED for v in tdf["Impact"]],
                text=[f"{v:+.1f}" for v in tdf["Impact"]],
                textposition="outside",
            ))
            fig_t.add_vline(x=0, line_dash="dash",
                            line_color=WHO_GRAY, line_width=1)
            fig_t.update_layout(**_L,
                title="Individual Lever Contributions",
                xaxis_title="MMR reduction (positive = fewer deaths)")
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("Adjust at least one lever to see the tornado chart.")

    st.markdown('<div class="sec-hdr">Policy Input Summary</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Indicator":       ["GDP per Capita (USD)", "Health Expenditure (USD)",
                            "Fertility Rate",        "Female Education (%)"],
        "Baseline":        [f"${b_vals['gdp_per_capita']:,.0f}",
                            f"${b_vals['health_expenditure_per_capita']:,.0f}",
                            f"{b_vals['fertility_rate']:.2f}",
                            f"{b_vals['female_secondary_enrollment']:.1f}%"],
        "Policy Scenario": [f"${s_vals['gdp_per_capita']:,.0f}  ({gdp_pct:+d}%)",
                            f"${s_vals['health_expenditure_per_capita']:,.0f}  ({health_pct:+d}%)",
                            f"{s_vals['fertility_rate']:.2f}  ({fert_pct:+d}%)",
                            f"{s_vals['female_secondary_enrollment']:.1f}%  ({edu_pct:+d}%)"],
    }), use_container_width=True, hide_index=True)
    st.caption(f"Model: {model_choice}  ·  Country: {country}  ·  Reference year: {year}")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:{WHO_GRAY};font-size:0.8rem;padding:0.4rem 0 1rem;">
  <strong>MCH Policy Intelligence Dashboard</strong> &nbsp;·&nbsp;
  Data: World Health Organization (WHO) / World Bank &nbsp;·&nbsp;
  Prepared for the Ministry of Health, Ghana &nbsp;·&nbsp;
  MPhil Data Science · 2026<br>
  <span style="color:{WHO_BLUE};">
    Explainable AI (SHAP) &nbsp;·&nbsp;
    Panel Econometrics (Two-Way Fixed Effects) &nbsp;·&nbsp;
    ML Policy Simulation
  </span>
</div>
""", unsafe_allow_html=True)
