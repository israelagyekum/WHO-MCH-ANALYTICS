"""
Admin Panel — MCH Policy Intelligence Dashboard
Password-protected configuration manager.
Password: moh_ghana_2026  (override via st.secrets["ADMIN_PASSWORD"])
"""

import os
import json
import copy
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
APP_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

# ── WHO palette ───────────────────────────────────────────────────────────────
WHO_NAVY  = "#003F87"
WHO_BLUE  = "#009FD4"
WHO_GREEN = "#00A651"
WHO_RED   = "#E63329"
WHO_AMBER = "#F39200"
WHO_GRAY  = "#6D6E71"
WHO_WHITE = "#FFFFFF"
WHO_LIGHT = "#EFF6FB"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Admin Panel — MCH Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{ background-color: #F4F7FB; }}
  h1, h2, h3, h4 {{ color: {WHO_NAVY} !important; }}
  .stTabs [aria-selected="true"] {{
    background: {WHO_NAVY} !important;
    color: {WHO_WHITE} !important;
    border-radius: 8px 8px 0 0;
  }}
  .admin-hdr {{
    background: linear-gradient(90deg, {WHO_NAVY}, {WHO_BLUE});
    color: white; padding: 0.45rem 1rem; border-radius: 6px;
    font-weight: 700; font-size: 0.95rem;
    margin: 1.2rem 0 0.8rem; letter-spacing: 0.02em;
  }}
  .save-box {{
    background: {WHO_LIGHT}; border: 1px solid {WHO_BLUE};
    border-radius: 8px; padding: 1rem 1.2rem; margin-top: 1rem;
  }}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_admin_password() -> str:
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return "moh_ghana_2026"


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH GATE
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="background:linear-gradient(135deg,{WHO_NAVY} 0%,{WHO_BLUE} 100%);
            padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.5rem;">
  <div style="color:white;font-size:1.4rem;font-weight:800;">
    ⚙️ &nbsp;Admin Panel — MCH Policy Dashboard
  </div>
  <div style="color:rgba(255,255,255,0.8);font-size:0.85rem;margin-top:0.3rem;">
    Ministry of Health, Ghana &nbsp;·&nbsp; Restricted Access
  </div>
</div>
""", unsafe_allow_html=True)

if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    col_auth, _, _ = st.columns([1, 1, 1])
    with col_auth:
        st.markdown("### 🔐 Admin Login")
        pwd = st.text_input("Password", type="password", placeholder="Enter admin password")
        if st.button("Login", use_container_width=True, type="primary"):
            if pwd == get_admin_password():
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# ── Logout button ─────────────────────────────────────────────────────────────
col_hdr, col_logout = st.columns([8, 1])
with col_logout:
    if st.button("🚪 Logout"):
        st.session_state.admin_authed = False
        st.rerun()

# ── Load config ───────────────────────────────────────────────────────────────
cfg = load_config()


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN TABS
# ═══════════════════════════════════════════════════════════════════════════════
t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "🏷️ Branding",
    "🚨 Risk Thresholds",
    "🎯 WHO Benchmarks",
    "🤖 Model Settings",
    "📋 Policy Simulation",
    "🌍 Country Settings",
    "💾 Save & Export",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — BRANDING
# ─────────────────────────────────────────────────────────────────────────────
with t1:
    st.markdown('<div class="admin-hdr">🏷️ Dashboard Branding</div>', unsafe_allow_html=True)
    b = cfg["branding"]

    new_title    = st.text_input("Dashboard Title",    value=b["dashboard_title"])
    new_subtitle = st.text_area("Dashboard Subtitle",  value=b["dashboard_subtitle"], height=80)
    new_footer   = st.text_area("Footer Text",         value=b["footer_text"],        height=80)

    st.markdown('<div class="admin-hdr">Visible Tabs</div>', unsafe_allow_html=True)
    tab_names = {
        "global_overview":    "🌍 Global Overview",
        "country_analysis":   "🔬 Country Analysis",
        "econometric_models": "📊 Econometric Models",
        "xai_features":       "🤖 XAI & Feature Analysis",
        "policy_simulation":  "🎯 Policy Simulation",
    }
    show_tabs = {}
    cols = st.columns(len(tab_names))
    for i, (key, label) in enumerate(tab_names.items()):
        show_tabs[key] = cols[i].checkbox(label, value=b["show_tabs"].get(key, True))

    if st.button("💾 Apply Branding", type="primary"):
        cfg["branding"]["dashboard_title"]    = new_title
        cfg["branding"]["dashboard_subtitle"] = new_subtitle
        cfg["branding"]["footer_text"]        = new_footer
        cfg["branding"]["show_tabs"]          = show_tabs
        save_config(cfg)
        st.session_state["cfg_updated"] = True
        st.success("✅ Branding saved and applied to the live dashboard.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — RISK THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────
with t2:
    st.markdown('<div class="admin-hdr">🚨 MMR Risk Classification Thresholds</div>',
                unsafe_allow_html=True)
    rt = cfg["risk_thresholds"]

    st.info("These thresholds determine the coloured risk badges shown next to MMR metrics on the dashboard.")

    c1, c2, c3 = st.columns(3)
    new_high   = c1.number_input("High Risk — MMR above",   value=int(rt["high_mmr"]),   step=10)
    new_medium = c2.number_input("Moderate Risk — MMR above", value=int(rt["medium_mmr"]), step=10)
    new_low    = c3.number_input("Low Risk — MMR above",    value=int(rt["low_mmr"]),    step=5)

    st.markdown("**Preview of risk badges at these thresholds:**")
    for mmr_val, label in [(500, "500 MMR"), (250, "250 MMR"), (80, "80 MMR"), (30, "30 MMR")]:
        if mmr_val > new_high:
            color, badge = rt["colors"]["high"],     rt["labels"]["high"]
        elif mmr_val > new_medium:
            color, badge = rt["colors"]["medium"],   rt["labels"]["medium"]
        elif mmr_val > new_low:
            color, badge = rt["colors"]["low"],      rt["labels"]["low"]
        else:
            color, badge = rt["colors"]["very_low"], rt["labels"]["very_low"]
        st.markdown(
            f'<span style="background:{color};color:white;padding:2px 10px;'
            f'border-radius:12px;font-size:0.8rem;font-weight:700;">{badge}</span>'
            f'&nbsp; &nbsp;MMR = {mmr_val}',
            unsafe_allow_html=True)

    if st.button("💾 Apply Risk Thresholds", type="primary"):
        cfg["risk_thresholds"]["high_mmr"]   = new_high
        cfg["risk_thresholds"]["medium_mmr"] = new_medium
        cfg["risk_thresholds"]["low_mmr"]    = new_low
        save_config(cfg)
        st.session_state["cfg_updated"] = True
        st.success("✅ Risk thresholds saved.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — WHO BENCHMARKS
# ─────────────────────────────────────────────────────────────────────────────
with t3:
    st.markdown('<div class="admin-hdr">🎯 WHO / SDG Benchmark Lines</div>',
                unsafe_allow_html=True)
    wb = cfg["who_benchmarks"]

    st.info("Benchmark lines appear as dashed reference lines on all trend and comparison charts.")

    new_sdg_target = st.number_input(
        "SDG 3.1 MMR Target (per 100,000 live births)",
        value=float(wb["sdg_mmr_target"]), step=5.0)
    new_sdg_year   = st.number_input(
        "SDG Target Year", value=int(wb["sdg_target_year"]), step=1,
        min_value=2025, max_value=2050)
    new_sdg_label  = st.text_input("SDG Benchmark Label", value=wb["sdg_label"])

    st.markdown("---")
    new_min_health = st.number_input(
        "Minimum Health Expenditure (% of GDP) — WHO recommendation",
        value=float(wb["min_health_expenditure_pct_gdp"]), step=0.5,
        min_value=1.0, max_value=20.0)
    new_health_lbl = st.text_input(
        "Health Expenditure Benchmark Label", value=wb["min_health_exp_label"])

    new_show_lines = st.checkbox(
        "Show benchmark lines on all charts", value=wb["show_benchmark_lines"])

    if st.button("💾 Apply WHO Benchmarks", type="primary"):
        cfg["who_benchmarks"]["sdg_mmr_target"]              = new_sdg_target
        cfg["who_benchmarks"]["sdg_target_year"]             = new_sdg_year
        cfg["who_benchmarks"]["sdg_label"]                   = new_sdg_label
        cfg["who_benchmarks"]["min_health_expenditure_pct_gdp"] = new_min_health
        cfg["who_benchmarks"]["min_health_exp_label"]        = new_health_lbl
        cfg["who_benchmarks"]["show_benchmark_lines"]        = new_show_lines
        save_config(cfg)
        st.session_state["cfg_updated"] = True
        st.success("✅ WHO benchmarks saved.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — MODEL SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
with t4:
    st.markdown('<div class="admin-hdr">🤖 ML Model Configuration</div>',
                unsafe_allow_html=True)
    ms = cfg["model_settings"]

    st.warning("⚠️ Changing model parameters will retrain the model on next dashboard load (cached).")

    default_model = st.radio(
        "Default Active Model", ["Random Forest", "Gradient Boosting"],
        index=0 if ms["default_model"] == "Random Forest" else 1,
        horizontal=True)

    st.markdown("#### Random Forest")
    rf_col1, rf_col2, rf_col3 = st.columns(3)
    rf_n_est   = rf_col1.number_input("n_estimators",     value=ms["random_forest"]["n_estimators"],   step=10, min_value=10)
    rf_depth   = rf_col2.number_input("max_depth",        value=ms["random_forest"]["max_depth"],       step=1, min_value=1)
    rf_leaf    = rf_col3.number_input("min_samples_leaf", value=ms["random_forest"]["min_samples_leaf"],step=1, min_value=1)

    st.markdown("#### Gradient Boosting")
    gb_col1, gb_col2, gb_col3, gb_col4 = st.columns(4)
    gb_n_est = gb_col1.number_input("n_estimators",  value=ms["gradient_boosting"]["n_estimators"],  step=10, min_value=10)
    gb_lr    = gb_col2.number_input("learning_rate", value=ms["gradient_boosting"]["learning_rate"],  step=0.01, min_value=0.001, format="%.3f")
    gb_depth = gb_col3.number_input("max_depth",     value=ms["gradient_boosting"]["max_depth"],      step=1, min_value=1)
    gb_sub   = gb_col4.number_input("subsample",     value=ms["gradient_boosting"]["subsample"],      step=0.05, min_value=0.1, max_value=1.0)

    st.markdown("#### Training / Test Split")
    test_split = st.slider("Test set fraction", 0.1, 0.4, float(ms["test_split"]), step=0.05)

    if st.button("💾 Apply Model Settings", type="primary"):
        cfg["model_settings"]["default_model"]                          = default_model
        cfg["model_settings"]["random_forest"]["n_estimators"]          = int(rf_n_est)
        cfg["model_settings"]["random_forest"]["max_depth"]             = int(rf_depth)
        cfg["model_settings"]["random_forest"]["min_samples_leaf"]      = int(rf_leaf)
        cfg["model_settings"]["gradient_boosting"]["n_estimators"]      = int(gb_n_est)
        cfg["model_settings"]["gradient_boosting"]["learning_rate"]     = float(gb_lr)
        cfg["model_settings"]["gradient_boosting"]["max_depth"]         = int(gb_depth)
        cfg["model_settings"]["gradient_boosting"]["subsample"]         = float(gb_sub)
        cfg["model_settings"]["test_split"]                             = float(test_split)
        save_config(cfg)
        st.session_state["cfg_updated"] = True
        st.success("✅ Model settings saved. Dashboard will retrain on next load.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — POLICY SIMULATION
# ─────────────────────────────────────────────────────────────────────────────
with t5:
    st.markdown('<div class="admin-hdr">📋 Policy Simulation Configuration</div>',
                unsafe_allow_html=True)
    ps = cfg["policy_simulation"]

    st.markdown("#### Slider Ranges")
    sliders = [
        ("gdp_pct",      "💰 GDP per Capita Change (%)"),
        ("health_pct",   "🏥 Health Expenditure Change (%)"),
        ("fertility_pct","👶 Fertility Rate Change (%)"),
        ("education_pct","📚 Female Secondary Enrolment Change (%)"),
    ]
    new_ranges = {}
    for key, label in sliders:
        r = ps["slider_ranges"][key]
        cols = st.columns([3, 1, 1, 1])
        cols[0].markdown(f"**{label}**")
        mn   = cols[1].number_input(f"Min ({key})",  value=int(r["min"]),  step=5, key=f"min_{key}")
        mx   = cols[2].number_input(f"Max ({key})",  value=int(r["max"]),  step=5, key=f"max_{key}")
        stp  = cols[3].number_input(f"Step ({key})", value=int(r["step"]), step=1, key=f"stp_{key}", min_value=1)
        new_ranges[key] = {"min": mn, "max": mx, "step": stp}

    st.markdown("---")
    st.markdown("#### Government Scenario (one-click pre-load in Policy Simulation tab)")
    gs = ps["government_scenario"]
    gs_name    = st.text_input("Scenario Name", value=gs["name"])
    gc1, gc2, gc3, gc4 = st.columns(4)
    gs_gdp     = gc1.number_input("GDP % Change",         value=int(gs["gdp_pct"]),      step=5)
    gs_health  = gc2.number_input("Health Exp % Change",  value=int(gs["health_pct"]),   step=5)
    gs_fert    = gc3.number_input("Fertility % Change",   value=int(gs["fertility_pct"]),step=5)
    gs_edu     = gc4.number_input("Education % Change",   value=int(gs["education_pct"]),step=5)
    show_btn   = st.checkbox("Show Gov Scenario button on dashboard",
                              value=ps["show_gov_scenario_button"])

    if st.button("💾 Apply Policy Simulation Settings", type="primary"):
        cfg["policy_simulation"]["slider_ranges"]                 = new_ranges
        cfg["policy_simulation"]["government_scenario"]["name"]         = gs_name
        cfg["policy_simulation"]["government_scenario"]["gdp_pct"]      = int(gs_gdp)
        cfg["policy_simulation"]["government_scenario"]["health_pct"]   = int(gs_health)
        cfg["policy_simulation"]["government_scenario"]["fertility_pct"] = int(gs_fert)
        cfg["policy_simulation"]["government_scenario"]["education_pct"] = int(gs_edu)
        cfg["policy_simulation"]["show_gov_scenario_button"]     = show_btn
        save_config(cfg)
        st.session_state["cfg_updated"] = True
        st.success("✅ Policy simulation settings saved.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — COUNTRY SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
with t6:
    st.markdown('<div class="admin-hdr">🌍 Country Settings</div>', unsafe_allow_html=True)
    cs = cfg["country_settings"]

    # Default country
    new_default = st.text_input("Default Country on Load", value=cs["default_country"])

    # Policy recommendations
    st.markdown('<div class="admin-hdr">Policy Recommendations (per country)</div>',
                unsafe_allow_html=True)
    st.caption("These appear in the Country Analysis tab as a policy recommendation box.")
    pr = cs.get("policy_recommendations", {})
    countries_with_rec = list(pr.keys())
    all_editable = countries_with_rec + ["Add new country…"]
    sel_country = st.selectbox("Select country to edit", all_editable)

    if sel_country == "Add new country…":
        sel_country = st.text_input("Country name (exact match with data)")

    existing_rec = pr.get(sel_country, "")
    new_rec = st.text_area(f"Recommendation for {sel_country}", value=existing_rec, height=120)

    if st.button("💾 Save Recommendation", key="save_rec"):
        cfg["country_settings"]["policy_recommendations"][sel_country] = new_rec
        save_config(cfg)
        st.success(f"✅ Recommendation for {sel_country} saved.")

    # Peer groups
    st.markdown('<div class="admin-hdr">Peer Comparison Groups</div>',
                unsafe_allow_html=True)
    st.caption("Comma-separated list of peer countries for each focal country.")
    pg = cs.get("peer_groups", {})
    peer_country = st.selectbox("Country to configure peers", list(pg.keys()) + ["Add new…"],
                                key="peer_sel")
    if peer_country == "Add new…":
        peer_country = st.text_input("Country name", key="new_peer_country")
    existing_peers = ", ".join(pg.get(peer_country, []))
    new_peers_raw  = st.text_input(f"Peers for {peer_country}", value=existing_peers)

    if st.button("💾 Save Peer Group", key="save_peers"):
        cfg["country_settings"]["peer_groups"][peer_country] = [
            p.strip() for p in new_peers_raw.split(",") if p.strip()
        ]
        save_config(cfg)
        st.success(f"✅ Peer group for {peer_country} saved.")

    # Timeline annotations
    st.markdown('<div class="admin-hdr">Timeline Annotations</div>',
                unsafe_allow_html=True)
    st.caption("Vertical dashed lines added to country MMR trend charts.")
    ta = cs.get("timeline_annotations", {})
    ann_country = st.selectbox("Country", list(ta.keys()) + ["Add new…"], key="ann_sel")
    if ann_country == "Add new…":
        ann_country = st.text_input("Country name", key="new_ann_country")

    existing_anns = ta.get(ann_country, [])
    st.json(existing_anns)

    with st.expander("➕ Add annotation"):
        ann_year  = st.number_input("Year", value=2020, step=1, key="ann_yr")
        ann_label = st.text_input("Label",  key="ann_lbl")
        ann_color = st.color_picker("Colour", value="#009FD4", key="ann_clr")
        if st.button("Add annotation", key="add_ann"):
            if ann_country not in cfg["country_settings"]["timeline_annotations"]:
                cfg["country_settings"]["timeline_annotations"][ann_country] = []
            cfg["country_settings"]["timeline_annotations"][ann_country].append(
                {"year": int(ann_year), "label": ann_label, "color": ann_color})
            save_config(cfg)
            st.success("✅ Annotation added.")
            st.rerun()

    if st.button("💾 Save Default Country", type="primary"):
        cfg["country_settings"]["default_country"] = new_default
        save_config(cfg)
        st.session_state["cfg_updated"] = True
        st.success(f"✅ Default country set to {new_default}.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 — SAVE & EXPORT
# ─────────────────────────────────────────────────────────────────────────────
with t7:
    st.markdown('<div class="admin-hdr">💾 Save, Export & Reset</div>', unsafe_allow_html=True)

    current_cfg = load_config()

    # Export
    st.markdown("#### Export current config")
    cfg_json = json.dumps(current_cfg, indent=2, ensure_ascii=False)
    st.download_button(
        "⬇️ Download config.json",
        data=cfg_json,
        file_name="config.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("---")

    # Upload / restore
    st.markdown("#### Upload & restore config")
    uploaded = st.file_uploader("Upload config.json", type=["json"])
    if uploaded:
        try:
            restored = json.load(uploaded)
            st.json(restored)
            if st.button("✅ Apply uploaded config", type="primary"):
                save_config(restored)
                st.success("✅ Config restored from upload. Dashboard will reflect changes.")
                st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

    st.markdown("---")

    # Reset to defaults
    st.markdown("#### Reset to factory defaults")
    st.warning("This will overwrite all admin settings with the original defaults.")

    DEFAULTS = {
      "_comment": "MCH Policy Dashboard — Master Admin Config. Edit via Admin Panel or commit directly.",
      "branding": {
        "dashboard_title": "MCH Policy Intelligence Dashboard",
        "dashboard_subtitle": "Maternal & Child Health · WHO / World Bank Data · Ministry of Health, Ghana · Explainable AI · Panel Econometrics · Policy Simulation",
        "footer_text": "MCH Policy Intelligence Dashboard · Data: World Health Organization (WHO) / World Bank · Prepared for the Ministry of Health, Ghana · MPhil Data Science · 2026",
        "show_tabs": {
          "global_overview": True, "country_analysis": True,
          "econometric_models": True, "xai_features": True, "policy_simulation": True
        }
      },
      "risk_thresholds": {
        "high_mmr": 300, "medium_mmr": 100, "low_mmr": 50,
        "labels": {"high": "High Risk","medium": "Moderate Risk","low": "Low Risk","very_low": "On Track"},
        "colors": {"high": "#E63329","medium": "#F39200","low": "#009FD4","very_low": "#00A651"}
      },
      "who_benchmarks": {
        "sdg_mmr_target": 70, "sdg_target_year": 2030,
        "sdg_label": "SDG 3.1 Target (2030)",
        "min_health_expenditure_pct_gdp": 5.0,
        "min_health_exp_label": "WHO Min. Health Exp. Threshold (5% GDP)",
        "show_benchmark_lines": True
      },
      "model_settings": {
        "default_model": "Random Forest",
        "random_forest": {"n_estimators": 150, "max_depth": 8, "min_samples_leaf": 3},
        "gradient_boosting": {"n_estimators": 150, "learning_rate": 0.08, "max_depth": 4, "subsample": 0.8},
        "test_split": 0.2, "random_state": 42
      },
      "policy_simulation": {
        "slider_ranges": {
          "gdp_pct": {"min": -30, "max": 60, "step": 5},
          "health_pct": {"min": -30, "max": 100, "step": 5},
          "fertility_pct": {"min": -50, "max": 20, "step": 5},
          "education_pct": {"min": -20, "max": 60, "step": 5}
        },
        "government_scenario": {
          "name": "Ghana Health Sector Strategy 2030",
          "gdp_pct": 15, "health_pct": 40, "fertility_pct": -15, "education_pct": 25
        },
        "show_gov_scenario_button": True
      },
      "country_settings": {
        "default_country": "Ghana",
        "peer_groups": {
          "Ghana": ["Nigeria","Kenya","Senegal","Côte d'Ivoire","Cameroon"],
          "Kenya": ["Ghana","Tanzania","Uganda","Ethiopia","Rwanda"]
        },
        "policy_recommendations": {
          "Ghana": "Priority: Increase skilled birth attendance (currently ~87%). Expand Community Health Planning Services (CHPS) to underserved rural zones.",
          "Nigeria": "Priority: Strengthen primary healthcare infrastructure in the North. Accelerate female secondary education enrollment."
        },
        "timeline_annotations": {
          "Ghana": [
            {"year": 2003, "label": "NHIS Established", "color": "#009FD4"},
            {"year": 2008, "label": "Free Maternal Care Policy", "color": "#00A651"}
          ]
        }
      }
    }

    if st.button("🔄 Reset to defaults", type="secondary"):
        save_config(DEFAULTS)
        st.success("✅ Config reset to factory defaults.")
        st.rerun()

    st.markdown("---")
    st.markdown("#### Live config (read-only view)")
    st.json(current_cfg)

    # Status indicator
    if st.session_state.get("cfg_updated"):
        st.success("✅ Changes have been applied to config.json this session.")
        st.info(
            "To persist changes permanently across Streamlit Cloud deployments, "
            "download the updated config.json and commit it to your GitHub repository."
        )
