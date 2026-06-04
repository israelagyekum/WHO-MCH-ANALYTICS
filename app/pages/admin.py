"""
Admin Control Panel — MCH Policy Intelligence Dashboard
Password: moh_ghana_2026  (override via st.secrets["ADMIN_PASSWORD"])
"""
import os, json, copy
import streamlit as st

APP_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

WHO_NAVY  = "#003F87"; WHO_BLUE  = "#009FD4"; WHO_GREEN = "#00A651"
WHO_RED   = "#E63329"; WHO_AMBER = "#F39200"; WHO_GRAY  = "#6D6E71"
WHO_WHITE = "#FFFFFF"; WHO_LIGHT = "#EFF6FB"

st.set_page_config(page_title="Admin Panel — MCH Dashboard",
                   page_icon="⚙️", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown(f"""<style>
[data-testid="stAppViewContainer"]{{background-color:#F4F7FB;}}
h1,h2,h3,h4{{color:{WHO_NAVY} !important; font-family:'Segoe UI',Arial,sans-serif !important;}}
.stTabs [data-baseweb="tab-list"]{{gap:4px;background:{WHO_LIGHT};border-radius:10px 10px 0 0;padding:6px 6px 0;}}
.stTabs [data-baseweb="tab"]{{background:transparent;color:{WHO_GRAY};border-radius:8px 8px 0 0;font-weight:600;font-size:0.85rem;padding:8px 16px;border:none;}}
.stTabs [aria-selected="true"]{{background:{WHO_NAVY} !important;color:{WHO_WHITE} !important;}}
.adm{{background:linear-gradient(90deg,{WHO_NAVY},{WHO_BLUE});color:white;
  padding:0.45rem 1rem;border-radius:6px;font-weight:700;font-size:0.92rem;margin:1.1rem 0 0.8rem;}}
[data-testid="metric-container"]{{background:white;border-left:4px solid {WHO_BLUE};border-radius:8px;padding:0.5rem 0.8rem;}}
</style>""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_config():
    if "admin_cfg" in st.session_state and st.session_state["admin_cfg"]:
        return copy.deepcopy(st.session_state["admin_cfg"])
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        st.session_state["admin_cfg"] = cfg
        return copy.deepcopy(cfg)
    except Exception:
        return {}

def save_config(cfg):
    st.session_state["admin_cfg"]   = cfg
    st.session_state["cfg_updated"] = True
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False  # read-only on Cloud — session_state still applied

def get_password():
    try:    return st.secrets["ADMIN_PASSWORD"]
    except: return "moh_ghana_2026"


# ── Masthead ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,{WHO_NAVY} 0%,{WHO_BLUE} 100%);
            padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.5rem;">
  <div style="color:white;font-size:1.4rem;font-weight:800;">
    ⚙️ &nbsp;Admin Control Panel — MCH Policy Dashboard
  </div>
  <div style="color:rgba(255,255,255,0.8);font-size:0.85rem;margin-top:0.3rem;">
    Ministry of Health, Ghana &nbsp;·&nbsp; Restricted Access &nbsp;·&nbsp;
    Changes take effect immediately on the Dashboard tab
  </div>
</div>""", unsafe_allow_html=True)


# ── Auth gate ─────────────────────────────────────────────────────────────────
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    _, col, _ = st.columns([1,1,1])
    with col:
        st.markdown(f"""
        <div style="background:white;border-radius:12px;padding:2rem;
                    box-shadow:0 4px 24px rgba(0,63,135,0.12);
                    border-top:4px solid {WHO_NAVY};">
          <div style="text-align:center;font-size:2rem;margin-bottom:0.5rem;">🔐</div>
          <div style="text-align:center;color:{WHO_NAVY};font-weight:700;font-size:1.1rem;margin-bottom:1rem;">
            Admin Login
          </div>
        </div>""", unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password", placeholder="Enter admin password",
                            label_visibility="collapsed")
        if st.button("Sign In →", use_container_width=True, type="primary"):
            if pwd == get_password():
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# Logged-in toolbar
c_back, c_status, c_out = st.columns([1, 5, 1])
with c_back:
    if st.button("\u2190 Dashboard", key="nav_back"):
        import streamlit.components.v1 as _stc
        _stc.html("<script>window.parent.location.pathname='/';</script>", height=0)
        st.stop()
with c_status:
    st.info("✅ Logged in as Admin — changes apply to the live dashboard immediately.")
with c_out:
    if st.button("Logout"):
        st.session_state.admin_authed = False
        st.rerun()

cfg = load_config()

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
t1,t2,t3,t4,t5,t6,t7,t8,t9 = st.tabs([
    "🏷️ Branding",
    "🚨 Risk Thresholds",
    "🎯 WHO Benchmarks",
    "🤖 Model Settings",
    "📋 Policy Simulation",
    "📊 Econometrics",
    "🔔 Alerts",
    "🌍 Country Settings",
    "💾 Save & Export",
])


# ── TAB 1  BRANDING ───────────────────────────────────────────────────────────
with t1:
    st.markdown('<div class="adm">🏷️ Dashboard Branding & Messaging</div>', unsafe_allow_html=True)
    b = cfg.get("branding", {})
    new_title    = st.text_input("Dashboard Title",   value=b.get("dashboard_title","MCH Policy Intelligence Dashboard"))
    new_subtitle = st.text_area("Subtitle / Tagline", value=b.get("dashboard_subtitle",""), height=70)
    new_footer   = st.text_area("Footer Text",        value=b.get("footer_text",""), height=70)
    st.markdown('<div class="adm">Show / Hide Dashboard Tabs</div>', unsafe_allow_html=True)
    TAB_MAP = {"global_overview":"🌍 Global Overview","country_analysis":"🔬 Country Analysis",
               "econometric_models":"📊 Econometric Models","xai_features":"🤖 XAI & Feature Analysis",
               "policy_simulation":"🎯 Policy Simulation"}
    cur_tabs = b.get("show_tabs", {})
    new_show = {}
    cols = st.columns(len(TAB_MAP))
    for i,(k,lbl) in enumerate(TAB_MAP.items()):
        new_show[k] = cols[i].checkbox(lbl, value=cur_tabs.get(k, True), key=f"st_{k}")
    if st.button("💾 Apply Branding", type="primary", key="btn_brand"):
        cfg.setdefault("branding",{})
        cfg["branding"].update({"dashboard_title":new_title,"dashboard_subtitle":new_subtitle,
                                "footer_text":new_footer,"show_tabs":new_show})
        save_config(cfg)
        st.success("✅ Applied! Switch to Dashboard tab to see changes.")


# ── TAB 2  RISK THRESHOLDS ────────────────────────────────────────────────────
with t2:
    st.markdown('<div class="adm">🚨 MMR Risk Classification Thresholds</div>', unsafe_allow_html=True)
    st.info("Coloured badges appear next to the MMR metric on the Country Analysis tab.")
    rt = cfg.get("risk_thresholds", {})
    c1,c2,c3 = st.columns(3)
    new_high   = c1.number_input("🔴 High Risk — MMR above",     value=int(rt.get("high_mmr",300)),   step=10)
    new_medium = c2.number_input("🟡 Moderate Risk — MMR above", value=int(rt.get("medium_mmr",100)), step=10)
    new_low    = c3.number_input("🟢 Low Risk — MMR above",      value=int(rt.get("low_mmr",50)),     step=5)

    st.markdown("**Live badge preview:**")
    clrs = rt.get("colors",{"high":WHO_RED,"medium":WHO_AMBER,"low":WHO_BLUE,"very_low":WHO_GREEN})
    lbls = rt.get("labels",{"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"})
    pcols = st.columns(4)
    for col, mmr in zip(pcols, [700, 300, 120, 40]):
        if   mmr > new_high:   c,l = clrs.get("high",   WHO_RED),   lbls.get("high",   "High Risk")
        elif mmr > new_medium: c,l = clrs.get("medium", WHO_AMBER), lbls.get("medium", "Moderate Risk")
        elif mmr > new_low:    c,l = clrs.get("low",    WHO_BLUE),  lbls.get("low",    "Low Risk")
        else:                   c,l = clrs.get("very_low",WHO_GREEN),lbls.get("very_low","On Track")
        col.markdown(f'<div style="text-align:center;">MMR = {mmr}<br>'
                     f'<span style="background:{c};color:white;padding:3px 12px;'
                     f'border-radius:12px;font-size:0.82rem;font-weight:700;">{l}</span></div>',
                     unsafe_allow_html=True)

    if st.button("💾 Apply Risk Thresholds", type="primary", key="btn_rt"):
        cfg.setdefault("risk_thresholds",{})
        cfg["risk_thresholds"]["high_mmr"]   = int(new_high)
        cfg["risk_thresholds"]["medium_mmr"] = int(new_medium)
        cfg["risk_thresholds"]["low_mmr"]    = int(new_low)
        save_config(cfg)
        st.success("✅ Risk thresholds applied.")


# ── TAB 3  WHO BENCHMARKS ─────────────────────────────────────────────────────
with t3:
    st.markdown('<div class="adm">🎯 WHO / SDG Benchmark Lines</div>', unsafe_allow_html=True)
    st.info("Green dashed benchmark line appears on all MMR trend and comparison charts.")
    wb = cfg.get("who_benchmarks", {})
    c1,c2,c3 = st.columns(3)
    new_sdg    = c1.number_input("SDG 3.1 MMR Target (per 100k)", value=float(wb.get("sdg_mmr_target",70)), step=5.0)
    new_yr     = c2.number_input("Target Year", value=int(wb.get("sdg_target_year",2030)), min_value=2025, max_value=2050)
    new_health = c3.number_input("Min Health Exp. (% GDP)", value=float(wb.get("min_health_expenditure_pct_gdp",5.0)), step=0.5)
    new_lbl    = st.text_input("Benchmark Label", value=wb.get("sdg_label","SDG 3.1 Target (2030)"))
    new_show   = st.checkbox("Show benchmark lines on all charts", value=wb.get("show_benchmark_lines", True))
    if st.button("💾 Apply WHO Benchmarks", type="primary", key="btn_wb"):
        cfg.setdefault("who_benchmarks",{})
        cfg["who_benchmarks"].update({"sdg_mmr_target":new_sdg,"sdg_target_year":int(new_yr),
                                      "sdg_label":new_lbl,"min_health_expenditure_pct_gdp":new_health,
                                      "show_benchmark_lines":new_show})
        save_config(cfg)
        st.success("✅ WHO benchmarks applied.")


# ── TAB 4  MODEL SETTINGS ─────────────────────────────────────────────────────
with t4:
    st.markdown('<div class="adm">🤖 ML Model Configuration</div>', unsafe_allow_html=True)
    st.warning("⚠️ Changing hyperparameters retrains the model on the next dashboard load.")
    ms      = cfg.get("model_settings", {})
    def_mdl = st.radio("Default Active Model", ["Random Forest","Gradient Boosting"],
                       index=0 if ms.get("default_model","Random Forest")=="Random Forest" else 1,
                       horizontal=True)
    st.markdown("#### 🌲 Random Forest")
    rf = ms.get("random_forest", {})
    rc1,rc2,rc3 = st.columns(3)
    rf_n = rc1.number_input("n_estimators",     value=int(rf.get("n_estimators",150)),    step=10, min_value=10, key="rf_n")
    rf_d = rc2.number_input("max_depth",        value=int(rf.get("max_depth",8)),          step=1,  min_value=2,  key="rf_d")
    rf_l = rc3.number_input("min_samples_leaf", value=int(rf.get("min_samples_leaf",3)),   step=1,  min_value=1,  key="rf_l")
    st.markdown("#### 📈 Gradient Boosting")
    gb = ms.get("gradient_boosting", {})
    gc1,gc2,gc3,gc4 = st.columns(4)
    gb_n   = gc1.number_input("n_estimators",  value=int(gb.get("n_estimators",150)),       step=10, min_value=10, key="gb_n")
    gb_lr  = gc2.number_input("learning_rate", value=float(gb.get("learning_rate",0.08)),   step=0.01, format="%.3f", key="gb_lr")
    gb_d   = gc3.number_input("max_depth",     value=int(gb.get("max_depth",4)),            step=1,  min_value=2,  key="gb_d")
    gb_sub = gc4.number_input("subsample",     value=float(gb.get("subsample",0.8)),        step=0.05, min_value=0.1, max_value=1.0, key="gb_sub")
    ts = st.slider("Test set fraction", 0.10, 0.40, float(ms.get("test_split",0.20)), step=0.05,
                   format="%.0f%%")
    if st.button("💾 Apply Model Settings", type="primary", key="btn_ms"):
        cfg.setdefault("model_settings",{})
        cfg["model_settings"]["default_model"] = def_mdl
        cfg["model_settings"]["random_forest"] = {"n_estimators":int(rf_n),"max_depth":int(rf_d),"min_samples_leaf":int(rf_l)}
        cfg["model_settings"]["gradient_boosting"] = {"n_estimators":int(gb_n),"learning_rate":float(gb_lr),"max_depth":int(gb_d),"subsample":float(gb_sub)}
        cfg["model_settings"]["test_split"] = float(ts)
        save_config(cfg)
        st.success("✅ Model settings applied. Dashboard will retrain on next load.")


# ── TAB 5  POLICY SIMULATION ──────────────────────────────────────────────────
with t5:
    st.markdown('<div class="adm">📋 Policy Simulation Controls</div>', unsafe_allow_html=True)
    ps = cfg.get("policy_simulation", {})
    sr = ps.get("slider_ranges", {})
    st.markdown("#### Slider Ranges")
    levers = [("gdp_pct","💰 GDP per Capita (%)"),("health_pct","🏥 Health Expenditure (%)"),
              ("fertility_pct","👶 Fertility Rate (%)"),("education_pct","📚 Female Education (%)")]
    new_ranges = {}
    for key, label in levers:
        r = sr.get(key, {"min":-30,"max":60,"step":5})
        lc,mnc,mxc = st.columns([3,1,1])
        lc.markdown(f"**{label}**")
        mn  = mnc.number_input("Min", value=int(r["min"]), step=5, key=f"mn_{key}")
        mx  = mxc.number_input("Max", value=int(r["max"]), step=5, key=f"mx_{key}")
        new_ranges[key] = {"min":mn,"max":mx,"step":r.get("step",5)}
    st.markdown("---")
    st.markdown("#### 🏛️ Government Scenario  *(one-click pre-load in Policy Simulation tab)*")
    gs      = ps.get("government_scenario", {})
    gs_name = st.text_input("Scenario Name", value=gs.get("name","Ghana Health Sector Strategy 2030"))
    gc1,gc2,gc3,gc4 = st.columns(4)
    gs_gdp  = gc1.number_input("GDP %",          value=int(gs.get("gdp_pct",15)),        step=5, key="gs_g")
    gs_hlt  = gc2.number_input("Health Exp %",   value=int(gs.get("health_pct",40)),     step=5, key="gs_h")
    gs_frt  = gc3.number_input("Fertility %",    value=int(gs.get("fertility_pct",-15)), step=5, key="gs_f")
    gs_edu  = gc4.number_input("Education %",    value=int(gs.get("education_pct",25)),  step=5, key="gs_e")
    show_btn = st.checkbox("Show Government Scenario button on dashboard",
                            value=ps.get("show_gov_scenario_button", True))
    if st.button("💾 Apply Policy Simulation Settings", type="primary", key="btn_ps"):
        cfg.setdefault("policy_simulation",{})
        cfg["policy_simulation"]["slider_ranges"]           = new_ranges
        cfg["policy_simulation"]["show_gov_scenario_button"] = show_btn
        cfg["policy_simulation"]["government_scenario"] = {
            "name":gs_name,"gdp_pct":int(gs_gdp),"health_pct":int(gs_hlt),
            "fertility_pct":int(gs_frt),"education_pct":int(gs_edu)
        }
        save_config(cfg)
        st.success("✅ Policy simulation settings applied.")


# ── TAB 6  ECONOMETRIC CONTROLS ───────────────────────────────────────────────
with t6:
    st.markdown('<div class="adm">📊 Econometric Model Controls</div>', unsafe_allow_html=True)
    ec = cfg.get("econometrics", {})

    st.markdown("#### Show / Hide Regression Tables")
    ec_c1, ec_c2 = st.columns(2)
    show_ols = ec_c1.checkbox("Show Pooled OLS table",       value=ec.get("show_ols", True))
    show_fe  = ec_c2.checkbox("Show Two-Way Fixed Effects table", value=ec.get("show_fe", True))

    st.markdown("#### Significance Level")
    sig_options = {"1% (α = 0.01)": 0.01, "5% (α = 0.05)": 0.05, "10% (α = 0.10)": 0.10}
    cur_sig = ec.get("significance_level", 0.05)
    cur_label = {0.01:"1% (α = 0.01)", 0.05:"5% (α = 0.05)", 0.10:"10% (α = 0.10)"}.get(cur_sig, "5% (α = 0.05)")
    sel_sig = st.radio("Significance level for coefficient stars",
                       list(sig_options.keys()), index=list(sig_options.keys()).index(cur_label),
                       horizontal=True)
    new_sig_val = sig_options[sel_sig]

    st.markdown("#### Variables in Regression Model")
    st.caption("Only checked variables will appear in OLS and Fixed Effects tables.")
    ALL_VARS = {
        "log_gdp":                   "log(GDP per Capita)",
        "log_health_exp":            "log(Health Expenditure per Capita)",
        "fertility_rate":            "Fertility Rate",
        "female_secondary_enrollment":"Female Secondary Enrollment (%)",
    }
    cur_vars = ec.get("features_in_model",list(ALL_VARS.keys()))
    new_vars = []
    var_cols = st.columns(2)
    for i,(k,lbl) in enumerate(ALL_VARS.items()):
        if var_cols[i%2].checkbox(lbl, value=(k in cur_vars), key=f"ev_{k}"):
            new_vars.append(k)
    if not new_vars:
        st.warning("⚠️ At least one variable must be selected.")
        new_vars = cur_vars

    if st.button("💾 Apply Econometric Settings", type="primary", key="btn_ec"):
        cfg.setdefault("econometrics",{})
        cfg["econometrics"]["show_ols"]           = show_ols
        cfg["econometrics"]["show_fe"]            = show_fe
        cfg["econometrics"]["significance_level"] = new_sig_val
        cfg["econometrics"]["features_in_model"]  = new_vars
        save_config(cfg)
        st.success("✅ Econometric settings applied. Return to Econometric Models tab.")


# ── TAB 7  ALERTS ─────────────────────────────────────────────────────────────
with t7:
    st.markdown('<div class="adm">🔔 Country Alert Management</div>', unsafe_allow_html=True)
    st.info("Active alerts appear as coloured banners on the Country Analysis tab when that country is selected.")
    alerts = cfg.get("alerts", [])

    # Display and edit existing alerts
    st.markdown(f"#### Current Alerts ({len(alerts)} configured)")
    if not alerts:
        st.caption("No alerts configured. Add one below.")

    to_delete = None
    for i, al in enumerate(alerts):
        with st.expander(f"{'🔴' if al.get('active',True) else '⬜'} {al.get('country','—')} — {al.get('message','')[:60]}…"):
            al_c1,al_c2,al_c3 = st.columns([2,1,1])
            alerts[i]["country"]   = al_c1.text_input("Country",   value=al.get("country",""),  key=f"al_cty_{i}")
            alerts[i]["threshold"] = al_c2.number_input("MMR Threshold", value=int(al.get("threshold",500)), step=10, key=f"al_thr_{i}")
            alerts[i]["color"]     = al_c3.color_picker("Colour",  value=al.get("color",WHO_RED), key=f"al_clr_{i}")
            alerts[i]["message"]   = st.text_area("Alert Message", value=al.get("message",""),  height=80, key=f"al_msg_{i}")
            alerts[i]["active"]    = st.checkbox("Active (show on dashboard)", value=al.get("active",True), key=f"al_act_{i}")
            if st.button("🗑️ Delete this alert", key=f"del_al_{i}"):
                to_delete = i

    if to_delete is not None:
        alerts.pop(to_delete)
        cfg["alerts"] = alerts
        save_config(cfg)
        st.rerun()

    st.markdown('<div class="adm">➕ Add New Alert</div>', unsafe_allow_html=True)
    na_c1,na_c2,na_c3 = st.columns([2,1,1])
    na_country   = na_c1.text_input("Country name (exact match)", placeholder="e.g. Nigeria")
    na_threshold = na_c2.number_input("MMR Threshold", value=500, step=10, min_value=1)
    na_color     = na_c3.color_picker("Alert Colour", value=WHO_RED)
    na_message   = st.text_area("Alert Message", placeholder="e.g. MMR exceeds WHO threshold — urgent action required.", height=80)
    na_active    = st.checkbox("Active immediately", value=True)

    if st.button("➕ Add Alert", type="primary", key="btn_add_al"):
        if na_country and na_message:
            cfg.setdefault("alerts",[]).append({
                "country":na_country,"threshold":int(na_threshold),
                "message":na_message,"color":na_color,"active":na_active
            })
            save_config(cfg)
            st.success(f"✅ Alert added for {na_country}.")
            st.rerun()
        else:
            st.warning("Please enter both a country name and a message.")


# ── TAB 8  COUNTRY SETTINGS ───────────────────────────────────────────────────
with t8:
    st.markdown('<div class="adm">🌍 Country & Data Settings</div>', unsafe_allow_html=True)
    cs = cfg.get("country_settings", {})

    # Default country
    new_default = st.text_input("Default Country on Load", value=cs.get("default_country","Ghana"))
    if st.button("💾 Set Default Country", key="btn_dc"):
        cfg.setdefault("country_settings",{})
        cfg["country_settings"]["default_country"] = new_default
        save_config(cfg)
        st.success(f"✅ Default country set to {new_default}.")

    # CSV upload
    st.markdown('<div class="adm">📂 Upload New Dataset (CSV)</div>', unsafe_allow_html=True)
    st.caption("Upload a replacement CSV. Required columns: country, year, maternal_mortality, gdp_per_capita, health_expenditure_per_capita, fertility_rate, female_secondary_enrollment")
    uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_csv:
        import pandas as pd, numpy as np
        try:
            udf = pd.read_csv(uploaded_csv)
            required_cols = ["country","year","maternal_mortality","gdp_per_capita",
                             "health_expenditure_per_capita","fertility_rate","female_secondary_enrollment"]
            missing = [c for c in required_cols if c not in udf.columns]
            if missing:
                st.error(f"Missing columns: {missing}")
            else:
                udf = udf.dropna(subset=required_cols)
                udf["log_mmr"]        = np.log(udf["maternal_mortality"].clip(lower=1))
                udf["log_gdp"]        = np.log(udf["gdp_per_capita"].clip(lower=1))
                udf["log_health_exp"] = np.log(udf["health_expenditure_per_capita"].clip(lower=1))
                st.success(f"✅ Preview: {len(udf):,} rows · {udf['country'].nunique()} countries · {udf['year'].min()}–{udf['year'].max()}")
                st.dataframe(udf.head(5), use_container_width=True)
                if st.button("✅ Apply uploaded dataset to dashboard", type="primary"):
                    st.session_state["custom_df"] = udf
                    st.session_state["cfg_updated"] = True
                    st.success("Dataset applied. Return to Dashboard tab.")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    # Policy recommendations
    st.markdown('<div class="adm">📝 Policy Recommendations (per country)</div>', unsafe_allow_html=True)
    pr      = cs.get("policy_recommendations", {})
    pr_opts = list(pr.keys()) + ["➕ Add new country…"]
    pr_sel  = st.selectbox("Country to edit", pr_opts, key="pr_sel")
    if pr_sel == "➕ Add new country…":
        pr_sel = st.text_input("Country name", key="pr_new")
    if pr_sel and pr_sel != "➕ Add new country…":
        new_rec = st.text_area(f"Recommendation for {pr_sel}", value=pr.get(pr_sel,""), height=120)
        if st.button("💾 Save Recommendation", key="btn_rec"):
            cfg["country_settings"]["policy_recommendations"][pr_sel] = new_rec
            save_config(cfg)
            st.success(f"✅ Recommendation for {pr_sel} saved.")

    # Peer groups
    st.markdown('<div class="adm">🤝 Peer Comparison Groups</div>', unsafe_allow_html=True)
    pg      = cs.get("peer_groups", {})
    pg_opts = list(pg.keys()) + ["➕ New country…"]
    pg_sel  = st.selectbox("Country to configure peers", pg_opts, key="pg_sel")
    if pg_sel == "➕ New country…":
        pg_sel = st.text_input("Country name", key="pg_new")
    if pg_sel and pg_sel != "➕ New country…":
        existing      = ", ".join(pg.get(pg_sel, []))
        new_peers_raw = st.text_input(f"Peers for {pg_sel} (comma-separated)", value=existing)
        if st.button("💾 Save Peer Group", key="btn_pg"):
            cfg["country_settings"]["peer_groups"][pg_sel] = [p.strip() for p in new_peers_raw.split(",") if p.strip()]
            save_config(cfg)
            st.success(f"✅ Peer group for {pg_sel} saved.")

    # Timeline annotations
    st.markdown('<div class="adm">📌 Timeline Annotations</div>', unsafe_allow_html=True)
    st.caption("Vertical dotted lines on country MMR trend charts marking key policy events.")
    ta      = cs.get("timeline_annotations", {})
    ta_opts = list(ta.keys()) + ["➕ New…"]
    ann_cty = st.selectbox("Country", ta_opts, key="ann_sel")
    if ann_cty == "➕ New…":
        ann_cty = st.text_input("Country name", key="ann_new")
    if ann_cty and ann_cty != "➕ New…":
        anns     = ta.get(ann_cty, [])
        to_del_a = None
        for i, ann in enumerate(anns):
            ac1,ac2,ac3,ac4 = st.columns([1,3,1,1])
            anns[i]["year"]  = ac1.number_input("Year",   value=int(ann["year"]),  key=f"ay{i}", min_value=1990, max_value=2030)
            anns[i]["label"] = ac2.text_input("Label",   value=ann.get("label",""), key=f"al_a{i}")
            anns[i]["color"] = ac3.color_picker("Colour", value=ann.get("color","#009FD4"), key=f"ac{i}")
            if ac4.button("🗑️", key=f"da_{i}"):
                to_del_a = i
        if to_del_a is not None:
            anns.pop(to_del_a)
            cfg["country_settings"]["timeline_annotations"][ann_cty] = anns
            save_config(cfg)
            st.rerun()
        if st.button("➕ Add annotation", key="btn_add_a"):
            anns.append({"year":2024,"label":"New Event","color":"#009FD4"})
            cfg.setdefault("country_settings",{}).setdefault("timeline_annotations",{})[ann_cty] = anns
            save_config(cfg)
            st.rerun()


# ── TAB 9  SAVE & EXPORT ─────────────────────────────────────────────────────
with t9:
    st.markdown('<div class="adm">💾 Save, Export & Reset</div>', unsafe_allow_html=True)
    current = load_config()
    sc1,sc2 = st.columns(2)
    with sc1:
        st.markdown("#### ⬇️ Export config.json")
        st.markdown("Download and **push to GitHub** to make changes permanent across all sessions.")
        st.download_button("Download config.json",
                           data=json.dumps(current, indent=2, ensure_ascii=False),
                           file_name="config.json", mime="application/json",
                           use_container_width=True)
    with sc2:
        st.markdown("#### ⬆️ Import / restore config")
        uploaded = st.file_uploader("Upload config.json", type=["json"])
        if uploaded:
            try:
                restored = json.load(uploaded)
                if st.button("✅ Apply uploaded config", type="primary", key="btn_restore"):
                    save_config(restored)
                    st.success("✅ Config restored. Switch to Dashboard tab.")
                    st.rerun()
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    st.markdown("---")
    st.markdown("#### 🔄 Reset all settings to factory defaults")
    st.warning("This will overwrite all current admin settings.")
    if st.button("🔄 Reset to defaults", type="secondary", key="btn_reset"):
        DEFAULTS = {
            "branding":{"dashboard_title":"MCH Policy Intelligence Dashboard",
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
                "gradient_boosting":{"n_estimators":150,"learning_rate":0.08,"max_depth":4,"subsample":0.8},
                "test_split":0.2},
            "policy_simulation":{"slider_ranges":{
                "gdp_pct":{"min":-30,"max":60,"step":5},"health_pct":{"min":-30,"max":100,"step":5},
                "fertility_pct":{"min":-50,"max":20,"step":5},"education_pct":{"min":-20,"max":60,"step":5}},
                "government_scenario":{"name":"Ghana Health Sector Strategy 2030","gdp_pct":15,"health_pct":40,"fertility_pct":-15,"education_pct":25},
                "show_gov_scenario_button":True},
            "econometrics":{"show_ols":True,"show_fe":True,"significance_level":0.05,
                "features_in_model":["log_gdp","log_health_exp","fertility_rate","female_secondary_enrollment"]},
            "alerts":[],
            "country_settings":{"default_country":"Ghana",
                "peer_groups":{"Ghana":["Nigeria","Kenya","Senegal","Cameroon"]},
                "policy_recommendations":{"Ghana":"Priority: Increase skilled birth attendance. Target MMR < 70 by 2030 (SDG 3.1)."},
                "timeline_annotations":{"Ghana":[{"year":2003,"label":"NHIS Established","color":"#009FD4"},
                    {"year":2008,"label":"Free Maternal Care Policy","color":"#00A651"}]}}
        }
        save_config(DEFAULTS)
        st.success("✅ Reset to factory defaults.")
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Current live config")
    st.json(current)
    if st.session_state.get("cfg_updated"):
        st.success("✅ Changes are live this session. Download config.json above and push to GitHub to persist permanently.")
