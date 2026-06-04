"""
MCH Policy Intelligence Dashboard
Maternal & Child Health — WHO Data | Ministry of Health, Ghana
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH   = os.path.join(ROOT, "data", "processed", "mch_panel_data.csv")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
sys.path.insert(0, ROOT)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib; matplotlib.use("Agg")
import shap
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.inspection import partial_dependence
import statsmodels.formula.api as smf
import statsmodels.api as sm

# WHO Official Colours
WHO_NAVY  = "#003F87"; WHO_BLUE  = "#009FD4"; WHO_GREEN = "#00A651"
WHO_RED   = "#E63329"; WHO_AMBER = "#F39200"; WHO_GRAY  = "#6D6E71"
WHO_LIGHT = "#EFF6FB"; WHO_WHITE = "#FFFFFF"
COLOR_SEQ = [WHO_NAVY, WHO_BLUE, WHO_GREEN, WHO_AMBER, WHO_RED, "#5C6BC0", "#AB47BC"]

FEATURES = ["gdp_per_capita","fertility_rate",
            "health_expenditure_per_capita","female_secondary_enrollment"]
FEAT_LBL = {
    "gdp_per_capita":                "GDP per Capita (USD)",
    "fertility_rate":                "Fertility Rate",
    "health_expenditure_per_capita": "Health Expenditure per Capita (USD)",
    "female_secondary_enrollment":   "Female Secondary Enrollment (%)",
}
TARGET = "maternal_mortality"

st.set_page_config(page_title="MCH Policy Dashboard — Ghana MoH",
                   page_icon="🏥", layout="wide",
                   initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
# NOTE: sidebar rules come LAST so they override the global h1-h4 navy colour
st.markdown(f"""<style>
[data-testid="stAppViewContainer"] {{ background-color: #F4F7FB; }}

/* Global headers (main content area) */
h1,h2,h3,h4 {{
  color: {WHO_NAVY} !important;
  font-family: 'Segoe UI', Arial, sans-serif !important;
}}

/* Metric cards */
[data-testid="metric-container"] {{
  background:{WHO_WHITE}; border:1px solid #D6E8F7;
  border-left:5px solid {WHO_BLUE}; border-radius:8px;
  padding:0.75rem 1rem; box-shadow:0 2px 8px rgba(0,63,135,0.07);
}}
[data-testid="stMetricValue"] {{
  color:{WHO_NAVY} !important; font-weight:700; font-size:1.5rem !important;
}}
[data-testid="stMetricLabel"] {{
  color:{WHO_GRAY} !important; font-size:0.75rem !important; text-transform:uppercase;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  gap:4px; background:{WHO_LIGHT}; border-radius:10px 10px 0 0; padding:6px 6px 0;
}}
.stTabs [data-baseweb="tab"] {{
  background:transparent; color:{WHO_GRAY}; border-radius:8px 8px 0 0;
  font-weight:600; font-size:0.85rem; padding:8px 18px; border:none;
}}
.stTabs [aria-selected="true"] {{
  background:{WHO_NAVY} !important; color:{WHO_WHITE} !important;
}}

/* Section headers */
.sec-hdr {{
  background:linear-gradient(90deg,{WHO_NAVY},{WHO_BLUE}); color:white;
  padding:0.45rem 1rem; border-radius:6px; font-weight:700; font-size:0.95rem;
  margin:1.2rem 0 0.8rem;
}}

footer, #MainMenu {{ display:none !important; visibility:hidden; }}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR — placed LAST so it wins over global h1-h4 navy rule
   ═══════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {WHO_NAVY} 0%, #002060 100%) !important;
}}

/* ── Force every text node white ── */
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] em,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] button {{
  color: {WHO_WHITE} !important;
}}

/* ── Widget labels ── */
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{
  color: {WHO_WHITE} !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  letter-spacing: 0.01em;
}}

/* ── Selectbox container & value text ── */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background: rgba(255,255,255,0.18) !important;
  border: 1.5px solid rgba(255,255,255,0.55) !important;
  border-radius: 8px !important;
  color: {WHO_WHITE} !important;
}}
/* Selected value text — BaseWeb renders it in a nested div/span */
[data-testid="stSidebar"] [data-baseweb="select"] [class*="singleValue"],
[data-testid="stSidebar"] [data-baseweb="select"] [class*="placeholder"],
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] input {{
  color: {WHO_WHITE} !important;
  background: transparent !important;
  -webkit-text-fill-color: {WHO_WHITE} !important;
}}
/* Dropdown arrow icon */
[data-testid="stSidebar"] [data-baseweb="select"] svg {{
  fill: {WHO_WHITE} !important;
}}

/* ── Radio buttons ── */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {{
  background: rgba(255,255,255,0.10);
  border-radius: 8px; padding: 6px 10px;
  border: 1px solid rgba(255,255,255,0.2);
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{
  color: {WHO_WHITE} !important;
  font-size: 0.87rem !important;
}}
/* Active radio indicator */
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + span {{
  color: {WHO_BLUE} !important;
  font-weight: 700 !important;
}}

/* ── Sidebar page-navigation links ── */
[data-testid="stSidebarNav"] {{
  background: rgba(0,0,0,0.18);
  border-radius: 8px; padding: 4px; margin-bottom: 0.5rem;
}}
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] span {{
  color: rgba(255,255,255,0.92) !important;
  border-radius: 6px; padding: 6px 12px;
  font-weight: 600; font-size: 0.88rem;
  display: block; text-decoration: none;
}}
[data-testid="stSidebarNav"] a:hover {{
  background: rgba(0,159,212,0.35) !important;
}}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
  background: {WHO_BLUE} !important; color: {WHO_WHITE} !important;
}}

/* ── Admin / page-link button ── */
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] span {{
  background: rgba(0,159,212,0.28) !important;
  color: {WHO_WHITE} !important;
  border: 1.5px solid rgba(0,159,212,0.65) !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
  padding: 0.45rem 0.8rem !important;
  display: block !important;
  text-align: center !important;
  text-decoration: none !important;
  transition: background 0.2s;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover,
[data-testid="stSidebar"] [data-testid="stPageLink"] span:hover {{
  background: {WHO_BLUE} !important;
  border-color: {WHO_BLUE} !important;
}}
/* Fallback for old st.button style */
[data-testid="stSidebar"] [data-testid="stButton"] button {{
  background: rgba(0,159,212,0.28) !important;
  color: {WHO_WHITE} !important;
  border: 1.5px solid rgba(0,159,212,0.65) !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
  background: {WHO_BLUE} !important;
  border-color: {WHO_BLUE} !important;
}}

/* ── Horizontal rule ── */
[data-testid="stSidebar"] hr {{
  border-color: rgba(255,255,255,0.25) !important;
  margin: 0.6rem 0 !important;
}}

/* ── Markdown text in sidebar ── */
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown {{
  color: rgba(255,255,255,0.88) !important;
  font-size: 0.84rem !important;
  line-height: 1.6;
}}
[data-testid="stSidebar"] .stMarkdown strong,
[data-testid="stSidebar"] .stMarkdown b {{
  color: {WHO_WHITE} !important;
  font-weight: 700 !important;
}}
</style>""", unsafe_allow_html=True)


# ── Config helpers ─────────────────────────────────────────────────────────────
def get_cfg():
    """
    Priority order:
    1. If admin just saved (cfg_updated=True) → session_state already has the
       latest config; don't re-read from file (write may have failed on Cloud).
    2. If admin_cfg missing → first load, read from file.
    """
    if st.session_state.get("cfg_updated"):
        # Admin saved — trust session_state, clear the flag
        st.session_state["cfg_updated"] = False
    elif "admin_cfg" not in st.session_state:
        try:
            with open(CONFIG_PATH) as f:
                st.session_state["admin_cfg"] = json.load(f)
        except Exception:
            st.session_state["admin_cfg"] = {}
    return st.session_state.get("admin_cfg", {})

def risk_badge(mmr, cfg):
    rt   = cfg.get("risk_thresholds", {})
    clrs = rt.get("colors",  {"high":WHO_RED,"medium":WHO_AMBER,"low":WHO_BLUE,"very_low":WHO_GREEN})
    lbls = rt.get("labels",  {"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"})
    if   mmr > rt.get("high_mmr",   300): c,l = clrs["high"],     lbls["high"]
    elif mmr > rt.get("medium_mmr", 100): c,l = clrs["medium"],   lbls["medium"]
    elif mmr > rt.get("low_mmr",     50): c,l = clrs["low"],      lbls["low"]
    else:                                  c,l = clrs["very_low"], lbls["very_low"]
    return (f'<span style="background:{c};color:white;padding:3px 14px;'
            f'border-radius:12px;font-size:0.8rem;font-weight:700;">{l}</span>')

def sig_stars(p, level=0.05):
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""

def add_sdg_line(fig, cfg):
    wb = cfg.get("who_benchmarks", {})
    if wb.get("show_benchmark_lines", True):
        fig.add_hline(y=wb.get("sdg_mmr_target", 70), line_dash="dash",
                      line_color=WHO_GREEN, line_width=2,
                      annotation_text=wb.get("sdg_label","SDG 3.1 Target (2030)"),
                      annotation_font_color=WHO_GREEN, annotation_font_size=10)

def add_annotations(fig, country, cfg):
    ta = cfg.get("country_settings", {}).get("timeline_annotations", {})
    for ann in ta.get(country, []):
        fig.add_vline(x=ann["year"], line_dash="dot",
                      line_color=ann.get("color", WHO_BLUE), line_width=1.5,
                      annotation_text=ann.get("label",""),
                      annotation_font_size=9,
                      annotation_font_color=ann.get("color", WHO_BLUE))

def show_alerts(country, cfg):
    alerts = cfg.get("alerts", [])
    for al in alerts:
        if al.get("active", True) and al.get("country","") == country:
            color = al.get("color", WHO_RED)
            msg   = al.get("message", "")
            st.markdown(
                f'<div style="background:{color}18;border-left:4px solid {color};'
                f'padding:0.6rem 1rem;border-radius:6px;margin:0.5rem 0;">'
                f'<b style="color:{color};">⚠️ Alert — {country}</b><br>'
                f'<span style="color:#333;font-size:0.9rem;">{msg}</span></div>',
                unsafe_allow_html=True)


# ── Inline Admin Panel ────────────────────────────────────────────────────────
def _admin_password():
    try:    return st.secrets["ADMIN_PASSWORD"]
    except: return "moh_ghana_2026"

def _save_cfg(cfg):
    st.session_state["admin_cfg"] = cfg
    st.session_state["cfg_updated"] = False  # already in session_state
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # read-only on Cloud — session_state already updated

def _show_inline_admin():
    """Full admin panel rendered inline in the main content area."""
    WHO_N = WHO_NAVY; WHO_B = WHO_BLUE
    # ── Auth gate ─────────────────────────────────────────────────────────────
    if "admin_authed" not in st.session_state:
        st.session_state.admin_authed = False
    if not st.session_state.admin_authed:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{WHO_N} 0%,{WHO_B} 100%);
                    padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.5rem;">
          <div style="color:white;font-size:1.4rem;font-weight:800;">
            ⚙️ &nbsp;Admin Control Panel — MCH Policy Dashboard
          </div>
          <div style="color:rgba(255,255,255,0.8);font-size:0.85rem;margin-top:0.3rem;">
            Ministry of Health, Ghana &nbsp;·&nbsp; Restricted Access
          </div>
        </div>""", unsafe_allow_html=True)
        _, col, _ = st.columns([1,1,1])
        with col:
            st.markdown(f"""<div style="background:white;border-radius:12px;padding:2rem;
                box-shadow:0 4px 24px rgba(0,63,135,0.12);
                border-top:4px solid {WHO_N};text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">🔐</div>
                <div style="color:{WHO_N};font-weight:700;font-size:1.1rem;margin-bottom:1rem;">
                Admin Login</div></div>""", unsafe_allow_html=True)
            pwd = st.text_input("Password", type="password",
                                placeholder="Enter admin password",
                                label_visibility="collapsed")
            if st.button("Sign In →", use_container_width=True, type="primary"):
                if pwd == _admin_password():
                    st.session_state.admin_authed = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        return
    # ── Toolbar ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{WHO_N} 0%,{WHO_B} 100%);
                padding:1.2rem 2rem;border-radius:12px;margin-bottom:1rem;">
      <div style="color:white;font-size:1.4rem;font-weight:800;">
        ⚙️ &nbsp;Admin Control Panel — MCH Policy Dashboard
      </div>
      <div style="color:rgba(255,255,255,0.8);font-size:0.85rem;margin-top:0.3rem;">
        Ministry of Health, Ghana &nbsp;·&nbsp; Changes apply immediately
      </div>
    </div>""", unsafe_allow_html=True)
    cb, cs, co = st.columns([1,5,1])
    with cb:
        if st.button("← Dashboard", key="adm_back"):
            st.session_state["_admin_open"] = False
            st.rerun()
    with cs:
        st.info("✅ Logged in as Admin — all changes are live in this session.")
    with co:
        if st.button("Logout", key="adm_logout"):
            st.session_state.admin_authed = False
            st.rerun()
    cfg = get_cfg()
    adm_css = f"""<style>
    .adm{{background:linear-gradient(90deg,{WHO_N},{WHO_B});color:white;
      padding:0.45rem 1rem;border-radius:6px;font-weight:700;
      font-size:0.92rem;margin:1.1rem 0 0.8rem;}}
    </style>"""
    st.markdown(adm_css, unsafe_allow_html=True)
    t1,t2,t3,t4,t5,t6,t7,t8,t9 = st.tabs([
        "🏷️ Branding","🚨 Risk Thresholds","🎯 WHO Benchmarks",
        "🤖 Model Settings","📋 Policy Simulation","📊 Econometrics",
        "🔔 Alerts","🌍 Country Settings","💾 Save & Export",
    ])
    # ── TAB 1  BRANDING ───────────────────────────────────────────────────────
    with t1:
        st.markdown('<div class="adm">🏷️ Dashboard Branding & Messaging</div>', unsafe_allow_html=True)
        b = cfg.get("branding", {})
        nt = st.text_input("Dashboard Title", value=b.get("dashboard_title","MCH Policy Intelligence Dashboard"), key="adm_t")
        ns = st.text_area("Subtitle / Tagline", value=b.get("dashboard_subtitle",""), height=70, key="adm_s")
        nf = st.text_area("Footer Text", value=b.get("footer_text",""), height=70, key="adm_f")
        st.markdown('<div class="adm">Show / Hide Dashboard Tabs</div>', unsafe_allow_html=True)
        TAB_MAP = {"global_overview":"🌍 Global Overview","country_analysis":"🔬 Country Analysis",
                   "econometric_models":"📊 Econometric Models","xai_features":"🤖 XAI & Feature Analysis",
                   "policy_simulation":"🎯 Policy Simulation"}
        cur_tabs = b.get("show_tabs", {}); new_show = {}
        tcols = st.columns(len(TAB_MAP))
        for i,(k,lbl) in enumerate(TAB_MAP.items()):
            new_show[k] = tcols[i].checkbox(lbl, value=cur_tabs.get(k,True), key=f"adm_st_{k}")
        if st.button("💾 Apply Branding", type="primary", key="adm_btn_br"):
            cfg.setdefault("branding",{})
            cfg["branding"].update({"dashboard_title":nt,"dashboard_subtitle":ns,"footer_text":nf,"show_tabs":new_show})
            _save_cfg(cfg); st.success("✅ Applied!")
    # ── TAB 2  RISK THRESHOLDS ────────────────────────────────────────────────
    with t2:
        st.markdown('<div class="adm">🚨 MMR Risk Classification Thresholds</div>', unsafe_allow_html=True)
        st.info("Coloured badges appear next to the MMR metric on the Country Analysis tab.")
        rt = cfg.get("risk_thresholds",{})
        rc1,rc2,rc3 = st.columns(3)
        nh = rc1.number_input("🔴 High Risk — MMR above",   value=int(rt.get("high_mmr",300)),   step=10, key="adm_rh")
        nm = rc2.number_input("🟡 Moderate — MMR above",    value=int(rt.get("medium_mmr",100)), step=10, key="adm_rm")
        nl = rc3.number_input("🟢 Low Risk — MMR above",    value=int(rt.get("low_mmr",50)),     step=5,  key="adm_rl")
        clrs = rt.get("colors",{"high":WHO_RED,"medium":WHO_AMBER,"low":WHO_BLUE,"very_low":WHO_GREEN})
        lbls = rt.get("labels",{"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"})
        pcols = st.columns(4)
        for pcol, mmr in zip(pcols,[700,300,120,40]):
            if   mmr>nh: c,l = clrs.get("high",WHO_RED),   lbls.get("high","High Risk")
            elif mmr>nm: c,l = clrs.get("medium",WHO_AMBER),lbls.get("medium","Moderate Risk")
            elif mmr>nl: c,l = clrs.get("low",WHO_BLUE),   lbls.get("low","Low Risk")
            else:        c,l = clrs.get("very_low",WHO_GREEN),lbls.get("very_low","On Track")
            pcol.markdown(f'<div style="text-align:center">MMR={mmr}<br><span style="background:{c};color:white;padding:3px 10px;border-radius:12px;font-size:0.8rem;font-weight:700">{l}</span></div>', unsafe_allow_html=True)
        if st.button("💾 Apply Risk Thresholds", type="primary", key="adm_btn_rt"):
            cfg.setdefault("risk_thresholds",{})
            cfg["risk_thresholds"].update({"high_mmr":int(nh),"medium_mmr":int(nm),"low_mmr":int(nl)})
            _save_cfg(cfg); st.success("✅ Risk thresholds updated.")
    # ── TAB 3  WHO BENCHMARKS ─────────────────────────────────────────────────
    with t3:
        st.markdown('<div class="adm">🎯 WHO / SDG Benchmark Lines</div>', unsafe_allow_html=True)
        wb = cfg.get("who_benchmarks",{})
        wc1,wc2,wc3 = st.columns(3)
        wsdg  = wc1.number_input("SDG 3.1 MMR Target (per 100k)", value=float(wb.get("sdg_mmr_target",70)), step=5.0, key="adm_wsdg")
        wyr   = wc2.number_input("Target Year", value=int(wb.get("sdg_target_year",2030)), min_value=2025, max_value=2050, key="adm_wyr")
        whexp = wc3.number_input("Min Health Exp. (% GDP)", value=float(wb.get("min_health_expenditure_pct_gdp",5.0)), step=0.5, key="adm_whexp")
        wlbl  = st.text_input("Benchmark Label", value=wb.get("sdg_label","SDG 3.1 Target (2030)"), key="adm_wlbl")
        wshow = st.checkbox("Show benchmark lines on all charts", value=wb.get("show_benchmark_lines",True), key="adm_wshow")
        if st.button("💾 Apply WHO Benchmarks", type="primary", key="adm_btn_wb"):
            cfg.setdefault("who_benchmarks",{})
            cfg["who_benchmarks"].update({"sdg_mmr_target":wsdg,"sdg_target_year":int(wyr),"sdg_label":wlbl,
                                          "min_health_expenditure_pct_gdp":whexp,"show_benchmark_lines":wshow})
            _save_cfg(cfg); st.success("✅ WHO benchmarks updated.")
    # ── TAB 4  MODEL SETTINGS ─────────────────────────────────────────────────
    with t4:
        st.markdown('<div class="adm">🤖 ML Model Configuration</div>', unsafe_allow_html=True)
        st.warning("⚠️ Changing hyperparameters retrains models on the next dashboard load.")
        ms2 = cfg.get("model_settings",{})
        def_mdl = st.radio("Default Active Model",["Random Forest","Gradient Boosting"],
                           index=0 if ms2.get("default_model","Random Forest")=="Random Forest" else 1,
                           horizontal=True, key="adm_mdl")
        st.markdown("#### 🌲 Random Forest")
        rf2 = ms2.get("random_forest",{}); mc1,mc2,mc3 = st.columns(3)
        rf_n = mc1.number_input("n_estimators",    value=int(rf2.get("n_estimators",150)), step=10, min_value=10, key="adm_rfn")
        rf_d = mc2.number_input("max_depth",       value=int(rf2.get("max_depth",8)),      step=1,  min_value=2,  key="adm_rfd")
        rf_l = mc3.number_input("min_samples_leaf",value=int(rf2.get("min_samples_leaf",3)),step=1, min_value=1,  key="adm_rfl")
        st.markdown("#### 📈 Gradient Boosting")
        gb2 = ms2.get("gradient_boosting",{}); gc1,gc2,gc3,gc4 = st.columns(4)
        gb_n  = gc1.number_input("n_estimators", value=int(gb2.get("n_estimators",150)),      step=10,  min_value=10, key="adm_gbn")
        gb_lr = gc2.number_input("learning_rate",value=float(gb2.get("learning_rate",0.08)),  step=0.01,format="%.3f",key="adm_gblr")
        gb_d  = gc3.number_input("max_depth",    value=int(gb2.get("max_depth",4)),           step=1,   min_value=2,  key="adm_gbd")
        gb_sub= gc4.number_input("subsample",    value=float(gb2.get("subsample",0.8)),       step=0.05,min_value=0.1,max_value=1.0,key="adm_gbs")
        ts2   = st.slider("Test set fraction", 0.10, 0.40, float(ms2.get("test_split",0.20)), step=0.05, key="adm_ts")
        if st.button("💾 Apply Model Settings", type="primary", key="adm_btn_ms"):
            cfg.setdefault("model_settings",{})
            cfg["model_settings"].update({"default_model":def_mdl,
                "random_forest":{"n_estimators":int(rf_n),"max_depth":int(rf_d),"min_samples_leaf":int(rf_l)},
                "gradient_boosting":{"n_estimators":int(gb_n),"learning_rate":float(gb_lr),"max_depth":int(gb_d),"subsample":float(gb_sub)},
                "test_split":float(ts2)})
            _save_cfg(cfg); st.success("✅ Model settings applied. Dashboard retrains on next load.")
    # ── TAB 5  POLICY SIMULATION ──────────────────────────────────────────────
    with t5:
        st.markdown('<div class="adm">📋 Policy Simulation Controls</div>', unsafe_allow_html=True)
        ps2 = cfg.get("policy_simulation",{}); sr2 = ps2.get("slider_ranges",{})
        levers = [("gdp_pct","💰 GDP (%)"),("health_pct","🏥 Health Exp (%)"),
                  ("fertility_pct","👶 Fertility (%)"),("education_pct","📚 Education (%)")]
        new_ranges = {}
        for key,label in levers:
            r = sr2.get(key,{"min":-30,"max":60,"step":5})
            lc,mnc,mxc = st.columns([3,1,1])
            lc.markdown(f"**{label}**")
            mn2 = mnc.number_input("Min",value=int(r["min"]),step=5,key=f"adm_mn_{key}")
            mx2 = mxc.number_input("Max",value=int(r["max"]),step=5,key=f"adm_mx_{key}")
            new_ranges[key] = {"min":mn2,"max":mx2,"step":r.get("step",5)}
        st.markdown("---"); st.markdown("#### 🏛️ Government Scenario")
        gs2 = ps2.get("government_scenario",{})
        gs_name = st.text_input("Scenario Name",value=gs2.get("name","Ghana Health Sector Strategy 2030"),key="adm_gsn")
        gg1,gg2,gg3,gg4 = st.columns(4)
        gs_gdp = gg1.number_input("GDP %",        value=int(gs2.get("gdp_pct",15)),       step=5,key="adm_gsg")
        gs_hlt = gg2.number_input("Health Exp %", value=int(gs2.get("health_pct",40)),    step=5,key="adm_gsh")
        gs_frt = gg3.number_input("Fertility %",  value=int(gs2.get("fertility_pct",-15)),step=5,key="adm_gsf")
        gs_edu = gg4.number_input("Education %",  value=int(gs2.get("education_pct",25)), step=5,key="adm_gse")
        show_btn = st.checkbox("Show Govt Scenario button on dashboard",
                               value=ps2.get("show_gov_scenario_button",True),key="adm_gsb")
        if st.button("💾 Apply Simulation Settings",type="primary",key="adm_btn_ps"):
            cfg.setdefault("policy_simulation",{})
            cfg["policy_simulation"].update({"slider_ranges":new_ranges,"show_gov_scenario_button":show_btn,
                "government_scenario":{"name":gs_name,"gdp_pct":int(gs_gdp),"health_pct":int(gs_hlt),
                                       "fertility_pct":int(gs_frt),"education_pct":int(gs_edu)}})
            _save_cfg(cfg); st.success("✅ Policy simulation settings applied.")
    # ── TAB 6  ECONOMETRICS ───────────────────────────────────────────────────
    with t6:
        st.markdown('<div class="adm">📊 Econometric Model Controls</div>', unsafe_allow_html=True)
        ec2 = cfg.get("econometrics",{})
        ec_c1,ec_c2 = st.columns(2)
        show_ols = ec_c1.checkbox("Show Pooled OLS table",      value=ec2.get("show_ols",True), key="adm_ols")
        show_fe  = ec_c2.checkbox("Show Fixed Effects table",   value=ec2.get("show_fe",True),  key="adm_fe")
        sig_opts = {"1% (α=0.01)":0.01,"5% (α=0.05)":0.05,"10% (α=0.10)":0.10}
        cur_sig  = ec2.get("significance_level",0.05)
        cur_lbl  = {0.01:"1% (α=0.01)",0.05:"5% (α=0.05)",0.10:"10% (α=0.10)"}.get(cur_sig,"5% (α=0.05)")
        sel_sig  = st.radio("Significance level",list(sig_opts.keys()),
                            index=list(sig_opts.keys()).index(cur_lbl),horizontal=True,key="adm_sig")
        st.markdown("#### Variables in Regression")
        ALL_VARS = {"log_gdp":"log(GDP per Capita)","log_health_exp":"log(Health Expenditure)",
                    "fertility_rate":"Fertility Rate","female_secondary_enrollment":"Female Education (%)"}
        cur_vars = ec2.get("features_in_model",list(ALL_VARS.keys())); new_vars = []
        var_cols2 = st.columns(2)
        for i,(k,lbl) in enumerate(ALL_VARS.items()):
            if var_cols2[i%2].checkbox(lbl,value=(k in cur_vars),key=f"adm_ev_{k}"): new_vars.append(k)
        if not new_vars: new_vars = cur_vars
        if st.button("💾 Apply Econometric Settings",type="primary",key="adm_btn_ec"):
            cfg.setdefault("econometrics",{})
            cfg["econometrics"].update({"show_ols":show_ols,"show_fe":show_fe,
                                        "significance_level":sig_opts[sel_sig],"features_in_model":new_vars})
            _save_cfg(cfg); st.success("✅ Econometric settings applied.")
    # ── TAB 7  ALERTS ─────────────────────────────────────────────────────────
    with t7:
        st.markdown('<div class="adm">🔔 Country Alert Management</div>', unsafe_allow_html=True)
        st.info("Active alerts appear as banners on the Country Analysis tab.")
        alerts = cfg.get("alerts",[])
        to_del = None
        for i,al in enumerate(alerts):
            with st.expander(f"{'🔴' if al.get('active',True) else '⬜'} {al.get('country','—')} — {al.get('message','')[:50]}…"):
                al_c1,al_c2,al_c3 = st.columns([2,1,1])
                alerts[i]["country"]   = al_c1.text_input("Country",value=al.get("country",""),key=f"adm_ac_{i}")
                alerts[i]["threshold"] = al_c2.number_input("MMR Threshold",value=int(al.get("threshold",500)),step=10,key=f"adm_at_{i}")
                alerts[i]["color"]     = al_c3.color_picker("Colour",value=al.get("color",WHO_RED),key=f"adm_acl_{i}")
                alerts[i]["message"]   = st.text_area("Message",value=al.get("message",""),height=70,key=f"adm_am_{i}")
                alerts[i]["active"]    = st.checkbox("Active",value=al.get("active",True),key=f"adm_aa_{i}")
                if st.button("🗑️ Delete",key=f"adm_del_{i}"): to_del = i
        if to_del is not None:
            alerts.pop(to_del); cfg["alerts"] = alerts; _save_cfg(cfg); st.rerun()
        st.markdown('<div class="adm">➕ Add New Alert</div>', unsafe_allow_html=True)
        na_c1,na_c2,na_c3 = st.columns([2,1,1])
        na_cty = na_c1.text_input("Country (exact)",placeholder="e.g. Nigeria",key="adm_nac")
        na_thr = na_c2.number_input("MMR Threshold",value=500,step=10,min_value=1,key="adm_nat")
        na_clr = na_c3.color_picker("Colour",value=WHO_RED,key="adm_nacl")
        na_msg = st.text_area("Alert Message",placeholder="e.g. Urgent intervention required.",height=70,key="adm_nam")
        na_act = st.checkbox("Active immediately",value=True,key="adm_naa")
        if st.button("➕ Add Alert",type="primary",key="adm_btn_al"):
            if na_cty and na_msg:
                cfg.setdefault("alerts",[]).append({"country":na_cty,"threshold":int(na_thr),
                                                     "message":na_msg,"color":na_clr,"active":na_act})
                _save_cfg(cfg); st.success(f"✅ Alert added for {na_cty}."); st.rerun()
            else: st.warning("Enter both a country and a message.")
    # ── TAB 8  COUNTRY SETTINGS ───────────────────────────────────────────────
    with t8:
        st.markdown('<div class="adm">🌍 Country & Data Settings</div>', unsafe_allow_html=True)
        cs2 = cfg.get("country_settings",{})
        new_def = st.text_input("Default Country on Load",value=cs2.get("default_country","Ghana"),key="adm_csd")
        if st.button("💾 Set Default Country",key="adm_btn_dc"):
            cfg.setdefault("country_settings",{})["default_country"] = new_def
            _save_cfg(cfg); st.success(f"✅ Default → {new_def}")
        st.markdown('<div class="adm">📂 Upload New Dataset (CSV)</div>', unsafe_allow_html=True)
        st.caption("Required columns: country, year, maternal_mortality, gdp_per_capita, health_expenditure_per_capita, fertility_rate, female_secondary_enrollment")
        ucsv = st.file_uploader("Upload CSV",type=["csv"],key="adm_ucsv")
        if ucsv:
            try:
                udf = pd.read_csv(ucsv)
                req = ["country","year","maternal_mortality","gdp_per_capita",
                       "health_expenditure_per_capita","fertility_rate","female_secondary_enrollment"]
                miss = [c for c in req if c not in udf.columns]
                if miss: st.error(f"Missing columns: {miss}")
                else:
                    udf = udf.dropna(subset=req)
                    udf["log_mmr"] = np.log(udf["maternal_mortality"].clip(lower=1))
                    udf["log_gdp"] = np.log(udf["gdp_per_capita"].clip(lower=1))
                    udf["log_health_exp"] = np.log(udf["health_expenditure_per_capita"].clip(lower=1))
                    st.success(f"✅ {len(udf):,} rows · {udf['country'].nunique()} countries")
                    st.dataframe(udf.head(5),use_container_width=True)
                    if st.button("✅ Apply uploaded dataset",type="primary",key="adm_apply_csv"):
                        st.session_state["custom_df"] = udf
                        st.session_state["cfg_updated"] = True
                        st.success("Dataset applied. Close admin to see dashboard update.")
            except Exception as e: st.error(f"Error: {e}")
        st.markdown('<div class="adm">📝 Policy Recommendations</div>', unsafe_allow_html=True)
        pr2 = cs2.get("policy_recommendations",{}); pr_opts = list(pr2.keys())+["➕ Add new…"]
        pr_sel = st.selectbox("Country to edit",pr_opts,key="adm_prsel")
        if pr_sel == "➕ Add new…": pr_sel = st.text_input("Country name",key="adm_prnew")
        if pr_sel and pr_sel != "➕ Add new…":
            new_rec = st.text_area(f"Recommendation for {pr_sel}",value=pr2.get(pr_sel,""),height=100,key="adm_rec")
            if st.button("💾 Save Recommendation",key="adm_btn_rec"):
                cfg.setdefault("country_settings",{}).setdefault("policy_recommendations",{})[pr_sel] = new_rec
                _save_cfg(cfg); st.success(f"✅ Recommendation for {pr_sel} saved.")
        st.markdown('<div class="adm">🤝 Peer Groups</div>', unsafe_allow_html=True)
        pg2 = cs2.get("peer_groups",{}); pg_opts = list(pg2.keys())+["➕ New…"]
        pg_sel = st.selectbox("Country",pg_opts,key="adm_pgsel")
        if pg_sel == "➕ New…": pg_sel = st.text_input("Country name",key="adm_pgnew")
        if pg_sel and pg_sel != "➕ New…":
            existing = ", ".join(pg2.get(pg_sel,[]))
            new_peers_raw = st.text_input(f"Peers for {pg_sel} (comma-separated)",value=existing,key="adm_peers")
            if st.button("💾 Save Peer Group",key="adm_btn_pg"):
                cfg.setdefault("country_settings",{}).setdefault("peer_groups",{})[pg_sel] = [p.strip() for p in new_peers_raw.split(",") if p.strip()]
                _save_cfg(cfg); st.success(f"✅ Peer group for {pg_sel} saved.")
    # ── TAB 9  SAVE & EXPORT ─────────────────────────────────────────────────
    with t9:
        st.markdown('<div class="adm">💾 Save, Export & Reset</div>', unsafe_allow_html=True)
        sc1,sc2 = st.columns(2)
        with sc1:
            st.markdown("#### ⬇️ Export config.json")
            st.download_button("Download config.json",
                               data=json.dumps(cfg,indent=2,ensure_ascii=False),
                               file_name="config.json",mime="application/json",
                               use_container_width=True,key="adm_dl")
        with sc2:
            st.markdown("#### ⬆️ Import config")
            upcfg = st.file_uploader("Upload config.json",type=["json"],key="adm_upcfg")
            if upcfg:
                try:
                    restored = json.load(upcfg)
                    if st.button("✅ Apply uploaded config",type="primary",key="adm_btn_restore"):
                        _save_cfg(restored); st.success("✅ Config restored."); st.rerun()
                except Exception as e: st.error(f"Invalid JSON: {e}")
        st.markdown("---"); st.markdown("#### 🔄 Reset to factory defaults")
        st.warning("This will overwrite all current admin settings.")
        if st.button("🔄 Reset to defaults",type="secondary",key="adm_btn_reset"):
            DEFAULTS = {"branding":{"dashboard_title":"MCH Policy Intelligence Dashboard",
                "dashboard_subtitle":"Maternal & Child Health · WHO / World Bank Data · Ministry of Health, Ghana",
                "footer_text":"MCH Policy Intelligence Dashboard · WHO / World Bank · Ministry of Health, Ghana · 2026",
                "show_tabs":{"global_overview":True,"country_analysis":True,"econometric_models":True,"xai_features":True,"policy_simulation":True}},
                "risk_thresholds":{"high_mmr":300,"medium_mmr":100,"low_mmr":50,
                "labels":{"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"},
                "colors":{"high":"#E63329","medium":"#F39200","low":"#009FD4","very_low":"#00A651"}},
                "who_benchmarks":{"sdg_mmr_target":70,"sdg_target_year":2030,"sdg_label":"SDG 3.1 Target (2030)",
                "min_health_expenditure_pct_gdp":5.0,"show_benchmark_lines":True},
                "model_settings":{"default_model":"Random Forest",
                "random_forest":{"n_estimators":150,"max_depth":8,"min_samples_leaf":3},
                "gradient_boosting":{"n_estimators":150,"learning_rate":0.08,"max_depth":4,"subsample":0.8},"test_split":0.2},
                "policy_simulation":{"slider_ranges":{"gdp_pct":{"min":-30,"max":60,"step":5},
                "health_pct":{"min":-30,"max":100,"step":5},"fertility_pct":{"min":-50,"max":20,"step":5},
                "education_pct":{"min":-20,"max":60,"step":5}},
                "government_scenario":{"name":"Ghana Health Sector Strategy 2030","gdp_pct":15,"health_pct":40,"fertility_pct":-15,"education_pct":25},
                "show_gov_scenario_button":True},
                "econometrics":{"show_ols":True,"show_fe":True,"significance_level":0.05,
                "features_in_model":["log_gdp","log_health_exp","fertility_rate","female_secondary_enrollment"]},
                "alerts":[],"country_settings":{"default_country":"Ghana",
                "peer_groups":{"Ghana":["Nigeria","Kenya","Senegal","Cameroon"]},
                "policy_recommendations":{"Ghana":"Priority: Increase skilled birth attendance. Target MMR < 70 by 2030."},
                "timeline_annotations":{"Ghana":[{"year":2003,"label":"NHIS Established","color":"#009FD4"},
                {"year":2008,"label":"Free Maternal Care Policy","color":"#00A651"}]}}}
            _save_cfg(DEFAULTS); st.success("✅ Reset to factory defaults."); st.rerun()
        st.markdown("---"); st.markdown("#### 📋 Current live config")
        st.json(cfg)

# ── Data & models ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_data_from_file(path):
    """Cached disk read — only runs once per session (or on path change)."""
    df = pd.read_csv(path)
    df = df.dropna(subset=FEATURES+[TARGET])
    df["log_mmr"]        = np.log(df[TARGET].clip(lower=1))
    df["log_gdp"]        = np.log(df["gdp_per_capita"].clip(lower=1))
    df["log_health_exp"] = np.log(df["health_expenditure_per_capita"].clip(lower=1))
    return df

def load_data():
    """
    Returns the active dataset.
    • Admin uploaded a CSV → returns that (session_state bypasses cache).
    • Otherwise → returns the cached WHO file from disk.
    session_state check is OUTSIDE the cached helper so @st.cache_data
    does not swallow the runtime check.
    """
    if "custom_df" in st.session_state:
        return st.session_state["custom_df"]
    return _load_data_from_file(DATA_PATH)

@st.cache_resource(show_spinner=False)
def train_models(_n, _rf, _gb, _ts):
    rfp = json.loads(_rf); gbp = json.loads(_gb)
    df  = pd.read_csv(DATA_PATH).dropna(subset=FEATURES+[TARGET])
    X,y = df[FEATURES], df[TARGET]
    Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=float(_ts),random_state=42)
    rf = RandomForestRegressor(**rfp, random_state=42, n_jobs=-1)
    rf.fit(Xtr,ytr); rp = rf.predict(Xte)
    gb = GradientBoostingRegressor(**gbp, random_state=42)
    gb.fit(Xtr,ytr); gp = gb.predict(Xte)
    def met(yt,yp): return {"r2":r2_score(yt,yp),"rmse":float(np.sqrt(mean_squared_error(yt,yp))),"mae":mean_absolute_error(yt,yp)}
    return dict(rf=rf,gb=gb,X_train=Xtr,X_test=Xte,y_train=ytr,y_test=yte,
                rf_metrics=met(yte,rp),gb_metrics=met(yte,gp))

@st.cache_data(show_spinner=False)
def run_econometrics(_n, _vars):
    df   = load_data()
    vars_in = json.loads(_vars)
    X_ols = sm.add_constant(df[vars_in])
    ols   = sm.OLS(df["log_mmr"], X_ols).fit(cov_type="HC3")
    var_str = " + ".join(vars_in)
    fe  = smf.ols(f"log_mmr ~ {var_str} + C(country) + C(year)",
                  data=df).fit(cov_type="cluster", cov_kwds={"groups": df["country"]})
    return ols, fe

# ── Bootstrap ──────────────────────────────────────────────────────────────────
with st.spinner("Loading WHO dataset…"):
    df  = load_data()
    cfg = get_cfg()

ms  = cfg.get("model_settings", {})
rfc = json.dumps(ms.get("random_forest",    {"n_estimators":150,"max_depth":8,"min_samples_leaf":3}), sort_keys=True)
gbc = json.dumps(ms.get("gradient_boosting",{"n_estimators":150,"learning_rate":0.08,"max_depth":4,"subsample":0.8}), sort_keys=True)
with st.spinner("Initialising models…"):
    models = train_models(len(df), rfc, gbc, ms.get("test_split", 0.2))

# ── Masthead ───────────────────────────────────────────────────────────────────
br   = cfg.get("branding", {})
T    = br.get("dashboard_title",    "MCH Policy Intelligence Dashboard")
S    = br.get("dashboard_subtitle", "Maternal & Child Health · WHO / World Bank Data · Ministry of Health, Ghana")
FOOT = br.get("footer_text",        "MCH Policy Intelligence Dashboard · WHO / World Bank · Ministry of Health, Ghana · 2026")

st.markdown(f"""
<div style="background:linear-gradient(135deg,{WHO_NAVY} 0%,{WHO_BLUE} 100%);
            padding:1.4rem 2rem;border-radius:12px;margin-bottom:1.2rem;
            box-shadow:0 4px 20px rgba(0,63,135,0.25);">
  <div style="color:white;font-size:1.65rem;font-weight:800;font-family:'Segoe UI',Arial,sans-serif;">
    🏥 &nbsp;{T}
  </div>
  <div style="color:rgba(255,255,255,0.85);font-size:0.9rem;margin-top:0.35rem;">{S}</div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 Dashboard Controls")
    st.markdown("---")
    cs_cfg  = cfg.get("country_settings", {})
    def_cty = cs_cfg.get("default_country", "Ghana")
    all_cty = sorted(df["country"].unique())
    def_idx = all_cty.index(def_cty) if def_cty in all_cty else 0
    country = st.selectbox("📍 Country", all_cty, index=def_idx)
    all_yrs = sorted(df["year"].unique())
    year    = st.selectbox("📅 Reference Year", all_yrs, index=len(all_yrs)-1)
    st.markdown("---")
    def_mdl = ms.get("default_model","Random Forest")
    mc      = st.radio("🤖 Active ML Model", ["Random Forest","Gradient Boosting"],
                       index=0 if def_mdl=="Random Forest" else 1)
    st.markdown("---")
    st.markdown(f"**Data:** WHO / World Bank  \n**Countries:** {df['country'].nunique()}  \n"
                f"**Period:** {df['year'].min()}–{df['year'].max()}  \n**Observations:** {len(df):,}")
    st.markdown("---")
    st.markdown("*Ministry of Health, Ghana*  \n*MPhil Data Science · 2026*")
    st.markdown("---")
    # Admin Panel — session-state toggle, no navigation or JS required
    if st.button("\u2699\ufe0f  Admin Panel", use_container_width=True, key="nav_admin"):
        st.session_state["_admin_open"] = not st.session_state.get("_admin_open", False)
        st.rerun()

# ── Inline admin panel ───────────────────────────────────────────────────────────
if st.session_state.get("_admin_open", False):
    _show_inline_admin()
    st.stop()

# ── Derived values ─────────────────────────────────────────────────────────────
am   = models["rf"] if mc == "Random Forest" else models["gb"]
amm  = models["rf_metrics"] if mc == "Random Forest" else models["gb_metrics"]
cdf  = df[df["country"] == country]
rdf  = cdf[cdf["year"] == year]
if rdf.empty: rdf = cdf.sort_values("year").iloc[[-1]]
row  = rdf.iloc[0]

_L   = dict(plot_bgcolor=WHO_WHITE, paper_bgcolor=WHO_WHITE,
            font=dict(family="Segoe UI,Arial", size=12, color="#2D3748"),
            title_font=dict(size=13, color=WHO_NAVY), margin=dict(t=50,b=40,l=40,r=20))

# Econometric config
ec     = cfg.get("econometrics", {})
SHOW_OLS = ec.get("show_ols", True)
SHOW_FE  = ec.get("show_fe",  True)
SIG_LVL  = float(ec.get("significance_level", 0.05))
VARS_IN  = ec.get("features_in_model", ["log_gdp","log_health_exp","fertility_rate","female_secondary_enrollment"])

def sig(p):
    if p < 0.01: return "***"
    if p < SIG_LVL: return "**" if SIG_LVL > 0.01 else "*"
    if p < 0.10: return "*"
    return ""

# Tab visibility
show_tabs = br.get("show_tabs", {})
tab_defs  = [("global_overview","🌍  Global Overview"),
             ("country_analysis","🔬  Country Analysis"),
             ("econometric_models","📊  Econometric Models"),
             ("xai_features","🤖  XAI & Feature Analysis"),
             ("policy_simulation","🎯  Policy Simulation")]
vis       = [l for k,l in tab_defs if show_tabs.get(k, True)]
tabs_list = st.tabs(vis)
tm        = {k: tabs_list[i] for i,(k,_) in enumerate(
             (kl for kl in tab_defs if show_tabs.get(kl[0], True)))}


# ══════════════════════════════════════════════════════════
# TAB 1  GLOBAL OVERVIEW
# ══════════════════════════════════════════════════════════
if "global_overview" in tm:
 with tm["global_overview"]:
  st.markdown('<div class="sec-hdr">🌍 Global Maternal Mortality Overview</div>', unsafe_allow_html=True)
  lat = df.sort_values("year").groupby("country", as_index=False).last()
  k1,k2,k3,k4,k5 = st.columns(5)
  k1.metric("Countries Tracked",     f"{df['country'].nunique()}")
  k2.metric("Global Avg MMR",        f"{lat[TARGET].mean():.0f}", help="per 100,000 live births")
  k3.metric("Avg Health Exp.",        f"${lat['health_expenditure_per_capita'].mean():.0f}")
  k4.metric("Avg Fertility Rate",     f"{lat['fertility_rate'].mean():.2f}")
  k5.metric("Avg Female Education",   f"{lat['female_secondary_enrollment'].mean():.1f}%")
  st.markdown("---")
  cm,ct = st.columns([3,2])
  with cm:
   fig_map = px.choropleth(lat, locations="country", locationmode="country names",
                            color=TARGET, title="Maternal Mortality Rate — Latest Available Year",
                            color_continuous_scale=["#EFF6FB",WHO_BLUE,WHO_NAVY,WHO_RED],
                            labels={TARGET:"MMR per 100k"})
   fig_map.update_layout(**_L,
       geo=dict(showframe=False,showcoastlines=True,projection_type="natural earth",bgcolor=WHO_WHITE),
       coloraxis_colorbar=dict(title="MMR<br>per 100k",title_font=dict(size=11)))
   st.plotly_chart(fig_map, use_container_width=True)
  with ct:
   t10 = lat.nlargest(10,TARGET)[["country",TARGET]].reset_index(drop=True)
   fig_top = px.bar(t10, x=TARGET, y="country", orientation="h",
                     title="Top 10 Highest MMR Countries",
                     color=TARGET, color_continuous_scale=[WHO_AMBER,WHO_RED],
                     labels={TARGET:"MMR per 100k","country":""})
   fig_top.update_layout(**_L, showlegend=False, yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
   st.plotly_chart(fig_top, use_container_width=True)
  gt = df.groupby("year")[TARGET].mean().reset_index()
  fig_gt = px.line(gt, x="year", y=TARGET, title="Global Average MMR Trend",
                    color_discrete_sequence=[WHO_BLUE], labels={TARGET:"MMR per 100k","year":"Year"})
  fig_gt.update_traces(line_width=3)
  add_sdg_line(fig_gt, cfg)
  fig_gt.update_layout(**_L, xaxis=dict(gridcolor="#E8EFF8"), yaxis=dict(gridcolor="#E8EFF8"))
  st.plotly_chart(fig_gt, use_container_width=True)
  st.markdown('<div class="sec-hdr">Key Correlations — All Countries</div>', unsafe_allow_html=True)
  fig_sc = px.scatter(lat, x="gdp_per_capita", y=TARGET, size="health_expenditure_per_capita",
                       color="fertility_rate", hover_name="country", log_x=True,
                       color_continuous_scale=[WHO_GREEN,WHO_AMBER,WHO_RED],
                       title="GDP per Capita vs MMR  (bubble = health spending · colour = fertility)",
                       labels={"gdp_per_capita":"GDP per Capita (USD, log scale)",
                               TARGET:"MMR per 100k","fertility_rate":"Fertility Rate"})
  fig_sc.update_layout(**_L)
  st.plotly_chart(fig_sc, use_container_width=True)


# ══════════════════════════════════════════════════════════
# TAB 2  COUNTRY ANALYSIS
# ══════════════════════════════════════════════════════════
if "country_analysis" in tm:
 with tm["country_analysis"]:
  st.markdown(f'<div class="sec-hdr">🔬 Country Deep Dive — {country}</div>', unsafe_allow_html=True)
  c1,c2,c3,c4,c5 = st.columns(5)
  c1.metric("Maternal Mortality",  f"{row[TARGET]:.0f}", help="per 100,000 live births")
  c2.metric("GDP per Capita",      f"${row['gdp_per_capita']:,.0f}")
  c3.metric("Health Expenditure",  f"${row['health_expenditure_per_capita']:,.0f}")
  c4.metric("Fertility Rate",      f"{row['fertility_rate']:.2f}")
  c5.metric("Female Education",    f"{row['female_secondary_enrollment']:.1f}%")
  st.markdown(f"<div style='margin:-0.3rem 0 0.8rem;'>Risk Level: &nbsp;{risk_badge(row[TARGET],cfg)}</div>",
              unsafe_allow_html=True)
  # Active alerts
  show_alerts(country, cfg)
  # Policy recommendation
  pr  = cs_cfg.get("policy_recommendations", {})
  rec = pr.get(country, "")
  if rec:
      st.info(f"**🏛️ Policy Recommendation — {country}**\n\n{rec}")
  st.markdown("---")
  ca,cb = st.columns(2)
  with ca:
   fig_a = px.area(cdf.sort_values("year"), x="year", y=TARGET,
                    title=f"Maternal Mortality Trend — {country}",
                    labels={TARGET:"MMR per 100k","year":"Year"},
                    color_discrete_sequence=[WHO_BLUE])
   fig_a.update_traces(fillcolor="rgba(0,159,212,0.1)", line_color=WHO_BLUE, line_width=2.5)
   add_sdg_line(fig_a, cfg); add_annotations(fig_a, country, cfg)
   fig_a.update_layout(**_L)
   st.plotly_chart(fig_a, use_container_width=True)
  with cb:
   fig_b = px.line(cdf.sort_values("year"), x="year", y="health_expenditure_per_capita",
                    title=f"Health Expenditure Trend — {country}",
                    labels={"health_expenditure_per_capita":"USD per capita","year":"Year"},
                    color_discrete_sequence=[WHO_GREEN])
   fig_b.update_traces(line_width=2.5)
   add_annotations(fig_b, country, cfg)
   fig_b.update_layout(**_L)
   st.plotly_chart(fig_b, use_container_width=True)
  st.markdown('<div class="sec-hdr">Regional / Peer Comparison</div>', unsafe_allow_html=True)
  pg        = cs_cfg.get("peer_groups", {})
  def_peers = [c for c in pg.get(country, []) if c in df["country"].unique()][:4]
  if country not in def_peers: def_peers = [country] + def_peers
  comp_sel  = st.multiselect("Countries to compare", sorted(df["country"].unique()), default=def_peers[:5])
  if comp_sel:
   fig_cp = px.line(df[df["country"].isin(comp_sel)].sort_values("year"),
                     x="year", y=TARGET, color="country",
                     title="MMR Comparison — Selected Countries",
                     color_discrete_sequence=COLOR_SEQ,
                     labels={TARGET:"MMR per 100k","year":"Year"})
   for tr in fig_cp.data:
       if tr.name == country: tr.line.width = 4; tr.line.color = WHO_RED
   add_sdg_line(fig_cp, cfg)
   fig_cp.update_layout(**_L)
   st.plotly_chart(fig_cp, use_container_width=True)
  ydf = df[df["year"]==year].copy()
  fig_s2 = px.scatter(ydf, x="gdp_per_capita", y=TARGET, hover_name="country",
                       size="health_expenditure_per_capita", color="fertility_rate",
                       log_x=True, color_continuous_scale=[WHO_GREEN,WHO_AMBER,WHO_RED],
                       title=f"GDP per Capita vs MMR ({year})",
                       labels={"gdp_per_capita":"GDP per Capita (USD, log scale)",
                               TARGET:"MMR per 100k","fertility_rate":"Fertility Rate"})
  if not rdf.empty:
      fig_s2.add_scatter(x=[row["gdp_per_capita"]], y=[row[TARGET]],
                         mode="markers+text", text=[f"  {country}"], textposition="middle right",
                         marker=dict(color=WHO_RED,size=16,symbol="star",line=dict(color=WHO_NAVY,width=2)),
                         showlegend=False)
  fig_s2.update_layout(**_L)
  st.plotly_chart(fig_s2, use_container_width=True)


# ══════════════════════════════════════════════════════════
# TAB 3  ECONOMETRIC MODELS
# ══════════════════════════════════════════════════════════
if "econometric_models" in tm:
 with tm["econometric_models"]:
  st.markdown('<div class="sec-hdr">📊 Panel Econometric Analysis</div>', unsafe_allow_html=True)
  vars_json = json.dumps(sorted(VARS_IN), sort_keys=True)
  with st.spinner("Running regressions…"):
      ols_m, fe_m = run_econometrics(len(df), vars_json)
  VAR_LBL = {"log_gdp":"log(GDP p.c.)","log_health_exp":"log(Health Exp.)",
             "fertility_rate":"Fertility Rate","female_secondary_enrollment":"Female Education"}

  if not SHOW_OLS and not SHOW_FE:
      st.info("Both OLS and Fixed Effects are hidden. Enable them in the Admin Panel → Econometrics tab.")
  cols_eco = st.columns([1,1] if (SHOW_OLS and SHOW_FE) else [1])

  if SHOW_OLS:
   with cols_eco[0]:
    st.markdown("#### Pooled OLS — Log-Log Specification")
    st.caption("Dep. var: ln(MMR)  |  Robust SE (HC3)")
    rows_o = [{"Variable":VAR_LBL.get(v,v),
               "Coef.":round(ols_m.params[v],4),
               "Std Err":round(ols_m.bse[v],4),
               "t":round(ols_m.tvalues[v],3),
               "p":round(ols_m.pvalues[v],4),
               "Sig.":sig(ols_m.pvalues[v])}
              for v in VARS_IN if v in ols_m.params.index]
    st.dataframe(pd.DataFrame(rows_o), use_container_width=True, hide_index=True)
    st.dataframe(pd.DataFrame({"Metric":["R²","Adj. R²","F-stat","N"],
        "Value":[f"{ols_m.rsquared:.4f}",f"{ols_m.rsquared_adj:.4f}",
                 f"{ols_m.fvalue:.2f}",f"{int(ols_m.nobs):,}"]}),
        use_container_width=True, hide_index=True)
    st.caption(f"Significance at {SIG_LVL*100:.0f}% level  |  *** p<0.01  ** p<0.05  * p<0.1")

  fe_col = cols_eco[1] if (SHOW_OLS and SHOW_FE) else cols_eco[0]
  if SHOW_FE:
   with fe_col:
    st.markdown("#### Two-Way Fixed Effects")
    st.caption("Country FE + Year FE  |  Clustered SE by country")
    rows_f = [{"Variable":VAR_LBL.get(v,v),
               "Coef.":round(fe_m.params[v],4),
               "Std Err":round(fe_m.bse[v],4),
               "t":round(fe_m.tvalues[v],3),
               "p":round(fe_m.pvalues[v],4),
               "Sig.":sig(fe_m.pvalues[v])}
              for v in VARS_IN if v in fe_m.params.index]
    st.dataframe(pd.DataFrame(rows_f), use_container_width=True, hide_index=True)
    st.dataframe(pd.DataFrame({"Metric":["Within R²","F-stat","N","Countries","Years"],
        "Value":[f"{fe_m.rsquared:.4f}",f"{fe_m.fvalue:.2f}",
                 f"{int(fe_m.nobs):,}",f"{df['country'].nunique()}",
                 f"{df['year'].nunique()}"]}),
        use_container_width=True, hide_index=True)
    st.caption(f"Significance at {SIG_LVL*100:.0f}% level  |  *** p<0.01  ** p<0.05  * p<0.1")

  if SHOW_OLS and SHOW_FE:
   st.markdown('<div class="sec-hdr">Coefficient Plot — OLS vs Fixed Effects (95% CI)</div>',
               unsafe_allow_html=True)
   crow = []
   for v in VARS_IN:
    for mdl,mn in [(ols_m,"Pooled OLS"),(fe_m,"Fixed Effects")]:
     if v in mdl.params.index:
      ci = mdl.conf_int().loc[v]
      crow.append(dict(Model=mn,Variable=VAR_LBL.get(v,v),
                       Coef=mdl.params[v],CI_lo=ci[0],CI_hi=ci[1]))
   cdf2 = pd.DataFrame(crow)
   fig_c = go.Figure()
   for mn,cl in [("Pooled OLS",WHO_BLUE),("Fixed Effects",WHO_NAVY)]:
    s = cdf2[cdf2["Model"]==mn]
    fig_c.add_trace(go.Scatter(x=s["Variable"],y=s["Coef"],
        error_y=dict(type="data",symmetric=False,
                     array=s["CI_hi"]-s["Coef"],arrayminus=s["Coef"]-s["CI_lo"],
                     thickness=2,width=6),
        mode="markers",marker=dict(size=11,color=cl,line=dict(color=WHO_WHITE,width=1.5)),name=mn))
   fig_c.add_hline(y=0,line_dash="dash",line_color=WHO_GRAY,line_width=1.2)
   # Build a one-off layout: start from _L then override margin so there's no duplicate key
   _L_coef = {**_L, "margin": dict(t=55, b=100, l=65, r=20)}
   fig_c.update_layout(
       **_L_coef,
       title=dict(
           text="Coefficient Estimates with 95% Confidence Intervals",
           font=dict(size=14, color=WHO_NAVY, family="Segoe UI, Arial"),
           x=0, xanchor="left", y=0.97, yanchor="top",
       ),
       xaxis=dict(
           title="Variable", tickangle=-20,
           tickfont=dict(size=11), gridcolor="#E8EFF8",
       ),
       yaxis=dict(
           title="Coefficient on ln(MMR)",
           gridcolor="#E8EFF8", zeroline=False,
       ),
       legend=dict(
           orientation="h", xanchor="center", x=0.5,
           yanchor="top", y=-0.22,
           bgcolor="rgba(255,255,255,0.85)",
           bordercolor="#D6E8F7", borderwidth=1,
           font=dict(size=12),
       ),
   )
   st.plotly_chart(fig_c, use_container_width=True)

   go_=ols_m.params.get("log_gdp",0); gf_=fe_m.params.get("log_gdp",0)
   ho_=ols_m.params.get("log_health_exp",0); hf_=fe_m.params.get("log_health_exp",0)
   fer_=fe_m.params.get("fertility_rate",0); edu_=fe_m.params.get("female_secondary_enrollment",0)
   st.markdown('<div class="sec-hdr">Economic Interpretation</div>', unsafe_allow_html=True)
   st.info(f"""
**GDP per Capita** — A 1% rise is associated with a **{abs(go_):.2f}% {'decrease' if go_<0 else 'increase'}** in MMR (OLS) and **{abs(gf_):.2f}% {'decrease' if gf_<0 else 'increase'}** (FE after country + year effects).

**Health Expenditure** — A 1% rise is associated with a **{abs(ho_):.2f}% {'decrease' if ho_<0 else 'increase'}** in MMR (OLS) vs **{abs(hf_):.2f}% {'decrease' if hf_<0 else 'increase'}** (FE).

**Fertility Rate** — Each unit rise: **{abs(fer_):.3f} {'decrease' if fer_<0 else 'increase'}** in ln(MMR) under FE.
**Female Education** — Each 1 pp: **{abs(edu_):.4f} {'decrease' if edu_<0 else 'increase'}** in ln(MMR) under FE.

> Two-way FE removes unobserved country heterogeneity and global time shocks, giving cleaner causal estimates.
""")


# ══════════════════════════════════════════════════════════
# TAB 4  XAI & FEATURE ANALYSIS
# ══════════════════════════════════════════════════════════
if "xai_features" in tm:
 with tm["xai_features"]:
  st.markdown('<div class="sec-hdr">🤖 Explainable AI — Model Interpretability</div>', unsafe_allow_html=True)
  m1,m2,m3,m4 = st.columns(4)
  m1.metric("Active Model", mc)
  m2.metric("R² (test)",    f"{amm['r2']:.4f}")
  m3.metric("RMSE",         f"{amm['rmse']:.2f}")
  m4.metric("MAE",          f"{amm['mae']:.2f}")
  st.markdown("#### Model Comparison")
  st.dataframe(pd.DataFrame({
      "Model":["Random Forest","Gradient Boosting"],
      "R²":   [models["rf_metrics"]["r2"],   models["gb_metrics"]["r2"]],
      "RMSE": [models["rf_metrics"]["rmse"], models["gb_metrics"]["rmse"]],
      "MAE":  [models["rf_metrics"]["mae"],  models["gb_metrics"]["mae"]],
  }).round(4), use_container_width=True, hide_index=True)
  st.markdown("---")
  cfi,csh = st.columns(2)
  with cfi:
   st.markdown("#### Feature Importance (Gini Impurity)")
   fi = pd.DataFrame({"Feature":[FEAT_LBL[f] for f in FEATURES],
                       "Importance":am.feature_importances_}).sort_values("Importance")
   fig_fi = go.Figure(go.Bar(x=fi["Importance"],y=fi["Feature"],orientation="h",
       marker=dict(color=fi["Importance"],colorscale=[[0,WHO_LIGHT],[0.5,WHO_BLUE],[1,WHO_NAVY]],showscale=False),
       text=[f"{v:.3f}" for v in fi["Importance"]],textposition="outside"))
   fig_fi.update_layout(**_L, title="Feature Importance", xaxis_title="Importance Score")
   st.plotly_chart(fig_fi, use_container_width=True)
  with csh:
   st.markdown("#### SHAP — Mean Absolute Impact")
   try:
    exp   = shap.TreeExplainer(models["rf"])
    sv    = exp.shap_values(models["X_test"])
    ms2   = np.abs(sv).mean(axis=0)
    shdf  = pd.DataFrame({"Feature":[FEAT_LBL[f] for f in FEATURES],"Mean |SHAP|":ms2}).sort_values("Mean |SHAP|")
    fig_sh = go.Figure(go.Bar(x=shdf["Mean |SHAP|"],y=shdf["Feature"],orientation="h",
                               marker_color=WHO_BLUE,
                               text=[f"{v:.1f}" for v in shdf["Mean |SHAP|"]],textposition="outside"))
    fig_sh.update_layout(**_L, title="Mean |SHAP| — Random Forest", xaxis_title="Mean |SHAP Value|")
    st.plotly_chart(fig_sh, use_container_width=True)
   except Exception as e:
    st.warning(f"SHAP error: {e}")
  st.markdown(f'<div class="sec-hdr">SHAP Waterfall — {country} ({year})</div>', unsafe_allow_html=True)
  try:
   exp  = shap.TreeExplainer(models["rf"])
   rf_  = pd.DataFrame([{f:row[f] for f in FEATURES}])
   sr_  = exp.shap_values(rf_)[0]
   wf   = pd.DataFrame({"Feature":[FEAT_LBL[f] for f in FEATURES],
                         "SHAP Value":sr_,"Feature Value":[row[f] for f in FEATURES]}).sort_values("SHAP Value")
   fig_wf = go.Figure(go.Bar(x=wf["SHAP Value"],y=wf["Feature"],orientation="h",
       marker_color=[WHO_GREEN if v<0 else WHO_RED for v in wf["SHAP Value"]],
       text=[f"val={v:.2f}" for v in wf["Feature Value"]],textposition="outside"))
   fig_wf.add_vline(x=0,line_color=WHO_GRAY,line_dash="dash",line_width=1.2)
   fig_wf.update_layout(**_L, title=f"SHAP Contributions — {country}",
                         xaxis_title="SHAP Value (impact on predicted MMR)")
   st.plotly_chart(fig_wf, use_container_width=True)
   st.caption(f"🟢 Green = reduces MMR  ·  🔴 Red = increases MMR  ·  Baseline = {exp.expected_value:.1f}")
  except Exception as e:
   st.warning(f"SHAP waterfall: {e}")
  st.markdown('<div class="sec-hdr">Partial Dependence Plot</div>', unsafe_allow_html=True)
  pf = st.selectbox("Select feature", FEATURES, format_func=lambda x: FEAT_LBL[x])
  try:
   pr2 = partial_dependence(models["rf"], models["X_test"],
                             features=[FEATURES.index(pf)], grid_resolution=60)
   pdd = pd.DataFrame({"Feature Value":pr2["grid_values"][0],"Predicted MMR":pr2["average"][0]})
   fig_pd = px.line(pdd, x="Feature Value", y="Predicted MMR",
                     title=f"Partial Dependence — {FEAT_LBL[pf]}",
                     color_discrete_sequence=[WHO_NAVY], labels={"Feature Value":FEAT_LBL[pf]})
   fig_pd.update_traces(line_width=3)
   fig_pd.add_vline(x=row[pf], line_dash="dot", line_color=WHO_RED, line_width=2,
                    annotation_text=f"{country}", annotation_font_color=WHO_RED)
   fig_pd.update_layout(**_L)
   st.plotly_chart(fig_pd, use_container_width=True)
  except Exception as e:
   st.warning(f"PDP: {e}")


# ══════════════════════════════════════════════════════════
# TAB 5  POLICY SIMULATION
# ══════════════════════════════════════════════════════════
if "policy_simulation" in tm:
 with tm["policy_simulation"]:
  st.markdown(f'<div class="sec-hdr">🎯 Policy Simulation — {country} · {year}</div>', unsafe_allow_html=True)
  st.markdown("Adjust policy levers to project the impact on Maternal Mortality Rate in real time.")
  psc = cfg.get("policy_simulation", {}); sr2 = psc.get("slider_ranges", {})
  gr2 = sr2.get("gdp_pct",       {"min":-30,"max":60, "step":5})
  hr2 = sr2.get("health_pct",    {"min":-30,"max":100,"step":5})
  fr2 = sr2.get("fertility_pct", {"min":-50,"max":20, "step":5})
  er2 = sr2.get("education_pct", {"min":-20,"max":60, "step":5})
  gs2 = psc.get("government_scenario", {})
  if psc.get("show_gov_scenario_button", True) and gs2:
      if st.button(f"🏛️ Load: {gs2.get('name','Government Scenario')}", type="secondary"):
          st.session_state["sim_gdp"]    = gs2.get("gdp_pct",    0)
          st.session_state["sim_health"] = gs2.get("health_pct", 0)
          st.session_state["sim_fert"]   = gs2.get("fertility_pct", 0)
          st.session_state["sim_edu"]    = gs2.get("education_pct", 0)
  sl1,sl2 = st.columns(2)
  with sl1:
   gp = st.slider("💰 GDP per Capita Change (%)",    gr2["min"],gr2["max"],st.session_state.get("sim_gdp",   0),step=gr2["step"])
   hp = st.slider("🏥 Health Expenditure Change (%)", hr2["min"],hr2["max"],st.session_state.get("sim_health",0),step=hr2["step"])
  with sl2:
   fp = st.slider("👶 Fertility Rate Change (%)",     fr2["min"],fr2["max"],st.session_state.get("sim_fert", 0),step=fr2["step"])
   ep = st.slider("📚 Female Enrolment Change (%)",   er2["min"],er2["max"],st.session_state.get("sim_edu",  0),step=er2["step"])
  sn  = st.text_input("📋 Scenario Name", "Custom Policy Scenario")
  bv  = {f:row[f] for f in FEATURES}
  sv2 = {"gdp_per_capita":                row["gdp_per_capita"]*(1+gp/100),
          "fertility_rate":                row["fertility_rate"]*(1+fp/100),
          "health_expenditure_per_capita": row["health_expenditure_per_capita"]*(1+hp/100),
          "female_secondary_enrollment":   row["female_secondary_enrollment"]*(1+ep/100)}
  bp  = am.predict(pd.DataFrame([bv])[FEATURES])[0]
  sp  = am.predict(pd.DataFrame([sv2])[FEATURES])[0]
  da  = bp - sp; dp = (sp-bp)/bp*100
  sdg = cfg.get("who_benchmarks",{}).get("sdg_mmr_target", 70)
  st.markdown("---"); st.markdown("### Simulation Results")
  r1,r2,r3,r4 = st.columns(4)
  r1.metric("Baseline MMR",      f"{bp:.1f}")
  r2.metric("Projected MMR",     f"{sp:.1f}", delta=f"{dp:+.1f}%", delta_color="inverse")
  r3.metric("MMR Change /100k",  f"{da:+.1f}", delta_color="inverse")
  r4.metric(f"vs SDG ({sdg:.0f})", f"{sp-sdg:+.1f}", delta_color="inverse")
  vz1,vz2 = st.columns(2)
  with vz1:
   bc = WHO_GREEN if sp<bp else WHO_RED
   fig_sm = go.Figure(go.Bar(x=["Baseline",sn],y=[bp,sp],marker_color=[WHO_BLUE,bc],
                              text=[f"{bp:.1f}",f"{sp:.1f}"],textposition="outside",width=0.45))
   fig_sm.add_hline(y=bp,line_dash="dot",line_color=WHO_GRAY,line_width=1.5)
   add_sdg_line(fig_sm, cfg)
   fig_sm.update_layout(**_L, title="Baseline vs Policy Scenario",
                         yaxis_title="MMR per 100,000 live births",
                         yaxis_range=[0,max(bp,sp)*1.25])
   st.plotly_chart(fig_sm, use_container_width=True)
  with vz2:
   tr2 = []
   for lb,cl,pc in [("💰 GDP","gdp_per_capita",gp),
                     ("🏥 Health","health_expenditure_per_capita",hp),
                     ("👶 Fertility","fertility_rate",fp),
                     ("📚 Education","female_secondary_enrollment",ep)]:
    if pc != 0:
     tmp = pd.DataFrame([bv])[FEATURES].copy()
     tmp[cl] = row[cl]*(1+pc/100)
     tr2.append({"Lever":lb,"Impact":bp-am.predict(tmp)[0]})
   if tr2:
    tdf2 = pd.DataFrame(tr2).sort_values("Impact")
    fig_t = go.Figure(go.Bar(x=tdf2["Impact"],y=tdf2["Lever"],orientation="h",
        marker_color=[WHO_GREEN if v>0 else WHO_RED for v in tdf2["Impact"]],
        text=[f"{v:+.1f}" for v in tdf2["Impact"]],textposition="outside"))
    fig_t.add_vline(x=0,line_dash="dash",line_color=WHO_GRAY,line_width=1)
    fig_t.update_layout(**_L, title="Individual Lever Contributions",
                         xaxis_title="MMR reduction (positive = fewer deaths)")
    st.plotly_chart(fig_t, use_container_width=True)
   else:
    st.info("Adjust at least one lever to see the tornado chart.")
  st.dataframe(pd.DataFrame({
      "Indicator":["GDP per Capita (USD)","Health Expenditure (USD)",
                   "Fertility Rate","Female Education (%)"],
      "Baseline":[f"${bv['gdp_per_capita']:,.0f}",
                  f"${bv['health_expenditure_per_capita']:,.0f}",
                  f"{bv['fertility_rate']:.2f}",
                  f"{bv['female_secondary_enrollment']:.1f}%"],
      "Policy Scenario":[f"${sv2['gdp_per_capita']:,.0f}  ({gp:+d}%)",
                         f"${sv2['health_expenditure_per_capita']:,.0f}  ({hp:+d}%)",
                         f"{sv2['fertility_rate']:.2f}  ({fp:+d}%)",
                         f"{sv2['female_secondary_enrollment']:.1f}%  ({ep:+d}%)"]}),
      use_container_width=True, hide_index=True)

# ── Footer ─────────────────────────────────────────────────────────────────

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""<div style="text-align:center;color:{WHO_GRAY};font-size:0.8rem;padding:0.4rem 0 1rem;">
  {FOOT}<br>
  <span style="color:{WHO_BLUE};">Explainable AI (SHAP) &nbsp;·&nbsp;
  Panel Econometrics (Two-Way Fixed Effects) &nbsp;·&nbsp;
  ML Policy Simulation</span>
</div>""", unsafe_allow_html=True)
