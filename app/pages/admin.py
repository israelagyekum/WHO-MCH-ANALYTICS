"""
Admin Panel — MCH Policy Intelligence Dashboard
Password-protected configuration manager.
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
h1,h2,h3,h4{{color:{WHO_NAVY} !important;}}
.stTabs [data-baseweb="tab-list"]{{gap:4px;background:{WHO_LIGHT};border-radius:10px 10px 0 0;padding:6px 6px 0;}}
.stTabs [data-baseweb="tab"]{{background:transparent;color:{WHO_GRAY};border-radius:8px 8px 0 0;font-weight:600;font-size:0.85rem;padding:8px 18px;border:none;}}
.stTabs [aria-selected="true"]{{background:{WHO_NAVY} !important;color:{WHO_WHITE} !important;border-radius:8px 8px 0 0;}}
.adm{{background:linear-gradient(90deg,{WHO_NAVY},{WHO_BLUE});color:white;
  padding:0.45rem 1rem;border-radius:6px;font-weight:700;font-size:0.95rem;margin:1.2rem 0 0.8rem;}}
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
    """Save to session_state instantly; try file (may be read-only on Cloud)."""
    st.session_state["admin_cfg"]   = cfg
    st.session_state["cfg_updated"] = True
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

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
    Ministry of Health, Ghana &nbsp;·&nbsp; Restricted Access
  </div>
</div>""", unsafe_allow_html=True)


# ── Auth gate ─────────────────────────────────────────────────────────────────
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False

if not st.session_state.admin_authed:
    col, _, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("### 🔐 Admin Login")
        pwd = st.text_input("Password", type="password", placeholder="Enter admin password")
        if st.button("Sign In", use_container_width=True, type="primary"):
            if pwd == get_password():
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# Logout
_, col_out = st.columns([9, 1])
with col_out:
    if st.button("🚪 Logout"):
        st.session_state.admin_authed = False
        st.rerun()

st.info("**Changes take effect immediately** on the Dashboard tab (same session). "
        "Download `config.json` from the Save & Export tab and push to GitHub to make them permanent.")

cfg = load_config()


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
t1,t2,t3,t4,t5,t6,t7 = st.tabs([
    "🏷️ Branding",
    "🚨 Risk Thresholds",
    "🎯 WHO Benchmarks",
    "🤖 Model Settings",
    "📋 Policy Simulation",
    "🌍 Country Settings",
    "💾 Save & Export",
])


# ── TAB 1  BRANDING ───────────────────────────────────────────────────────────
with t1:
    st.markdown('<div class="adm">🏷️ Dashboard Branding & Messaging</div>', unsafe_allow_html=True)
    b = cfg.get("branding", {})

    new_title    = st.text_input("Dashboard Title",   value=b.get("dashboard_title","MCH Policy Intelligence Dashboard"))
    new_subtitle = st.text_area("Subtitle / Tagline", value=b.get("dashboard_subtitle",""), height=70)
    new_footer   = st.text_area("Footer Text",        value=b.get("footer_text",""),        height=70)

    st.markdown('<div class="adm">Show / Hide Tabs</div>', unsafe_allow_html=True)
    TAB_KEYS = {
        "global_overview":    "🌍 Global Overview",
        "country_analysis":   "🔬 Country Analysis",
        "econometric_models": "📊 Econometric Models",
        "xai_features":       "🤖 XAI & Feature Analysis",
        "policy_simulation":  "🎯 Policy Simulation",
    }
    show_tabs_cfg = b.get("show_tabs", {})
    new_show = {}
    cols = st.columns(len(TAB_KEYS))
    for i, (k, lbl) in enumerate(TAB_KEYS.items()):
        new_show[k] = cols[i].checkbox(lbl, value=show_tabs_cfg.get(k, True), key=f"shtab_{k}")

    if st.button("💾 Apply Branding", type="primary", key="btn_brand"):
        cfg.setdefault("branding", {})
        cfg["branding"]["dashboard_title"]    = new_title
        cfg["branding"]["dashboard_subtitle"] = new_subtitle
        cfg["branding"]["footer_text"]        = new_footer
        cfg["branding"]["show_tabs"]          = new_show
        ok = save_config(cfg)
        st.success("✅ Applied! Switch to the Dashboard tab — changes are live.")


# ── TAB 2  RISK THRESHOLDS ────────────────────────────────────────────────────
with t2:
    st.markdown('<div class="adm">🚨 MMR Risk Classification Thresholds</div>', unsafe_allow_html=True)
    st.info("Coloured risk badges next to MMR metrics update immediately when you apply here.")
    rt = cfg.get("risk_thresholds", {})
    c1,c2,c3 = st.columns(3)
    new_high   = c1.number_input("🔴 High Risk — MMR above",    value=int(rt.get("high_mmr",300)),   step=10)
    new_medium = c2.number_input("🟡 Moderate Risk — MMR above",value=int(rt.get("medium_mmr",100)), step=10)
    new_low    = c3.number_input("🟢 Low Risk — MMR above",     value=int(rt.get("low_mmr",50)),     step=5)

    st.markdown("**Live badge preview:**")
    clrs = rt.get("colors", {"high":WHO_RED,"medium":WHO_AMBER,"low":WHO_BLUE,"very_low":WHO_GREEN})
    lbls = rt.get("labels", {"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"})
    prev_cols = st.columns(4)
    for col, mmr in zip(prev_cols, [600, 250, 80, 30]):
        if   mmr > new_high:   c,l = clrs.get("high",   WHO_RED),   lbls.get("high",   "High Risk")
        elif mmr > new_medium: c,l = clrs.get("medium", WHO_AMBER), lbls.get("medium", "Moderate Risk")
        elif mmr > new_low:    c,l = clrs.get("low",    WHO_BLUE),  lbls.get("low",    "Low Risk")
        else:                   c,l = clrs.get("very_low",WHO_GREEN),lbls.get("very_low","On Track")
        col.markdown(f'MMR = {mmr}<br><span style="background:{c};color:white;padding:2px 10px;'
                     f'border-radius:12px;font-size:0.8rem;font-weight:700;">{l}</span>',
                     unsafe_allow_html=True)

    if st.button("💾 Apply Risk Thresholds", type="primary", key="btn_rt"):
        cfg.setdefault("risk_thresholds", {})
        cfg["risk_thresholds"]["high_mmr"]   = int(new_high)
        cfg["risk_thresholds"]["medium_mmr"] = int(new_medium)
        cfg["risk_thresholds"]["low_mmr"]    = int(new_low)
        save_config(cfg)
        st.success("✅ Risk thresholds applied.")


# ── TAB 3  WHO BENCHMARKS ─────────────────────────────────────────────────────
with t3:
    st.markdown('<div class="adm">🎯 WHO / SDG Benchmark Lines</div>', unsafe_allow_html=True)
    st.info("Dashed reference lines appear on all trend and comparison charts.")
    wb = cfg.get("who_benchmarks", {})
    c1,c2,c3 = st.columns(3)
    new_sdg_target = c1.number_input("SDG 3.1 MMR Target (per 100k)", value=float(wb.get("sdg_mmr_target",70)), step=5.0)
    new_sdg_year   = c2.number_input("Target Year", value=int(wb.get("sdg_target_year",2030)), min_value=2025, max_value=2050)
    new_min_health = c3.number_input("Min Health Exp. (% GDP)",       value=float(wb.get("min_health_expenditure_pct_gdp",5.0)), step=0.5)
    new_sdg_label  = st.text_input("SDG Benchmark Label", value=wb.get("sdg_label","SDG 3.1 Target (2030)"))
    new_show_lines = st.checkbox("Show benchmark lines on all charts", value=wb.get("show_benchmark_lines", True))

    if st.button("💾 Apply WHO Benchmarks", type="primary", key="btn_wb"):
        cfg.setdefault("who_benchmarks", {})
        cfg["who_benchmarks"]["sdg_mmr_target"]              = new_sdg_target
        cfg["who_benchmarks"]["sdg_target_year"]             = int(new_sdg_year)
        cfg["who_benchmarks"]["sdg_label"]                   = new_sdg_label
        cfg["who_benchmarks"]["min_health_expenditure_pct_gdp"] = new_min_health
        cfg["who_benchmarks"]["show_benchmark_lines"]        = new_show_lines
        save_config(cfg)
        st.success("✅ WHO benchmarks applied.")


# ── TAB 4  MODEL SETTINGS ─────────────────────────────────────────────────────
with t4:
    st.markdown('<div class="adm">🤖 ML Model Configuration</div>', unsafe_allow_html=True)
    st.warning("⚠️ Changing these retrains the model on the next dashboard load.")
    ms = cfg.get("model_settings", {})
    def_mdl = st.radio("Default Active Model", ["Random Forest","Gradient Boosting"],
                       index=0 if ms.get("default_model","Random Forest")=="Random Forest" else 1,
                       horizontal=True)

    st.markdown("#### 🌲 Random Forest")
    rf = ms.get("random_forest", {})
    rfc1,rfc2,rfc3 = st.columns(3)
    rf_n   = rfc1.number_input("n_estimators",     value=int(rf.get("n_estimators",150)),    step=10, min_value=10,  key="rf_n")
    rf_d   = rfc2.number_input("max_depth",        value=int(rf.get("max_depth",8)),          step=1,  min_value=1,   key="rf_d")
    rf_l   = rfc3.number_input("min_samples_leaf", value=int(rf.get("min_samples_leaf",3)),   step=1,  min_value=1,   key="rf_l")

    st.markdown("#### 📈 Gradient Boosting")
    gb = ms.get("gradient_boosting", {})
    gbc1,gbc2,gbc3,gbc4 = st.columns(4)
    gb_n   = gbc1.number_input("n_estimators",  value=int(gb.get("n_estimators",150)),         step=10, min_value=10,  key="gb_n")
    gb_lr  = gbc2.number_input("learning_rate", value=float(gb.get("learning_rate",0.08)),     step=0.01, format="%.3f", key="gb_lr")
    gb_d   = gbc3.number_input("max_depth",     value=int(gb.get("max_depth",4)),              step=1,  min_value=1,   key="gb_d")
    gb_sub = gbc4.number_input("subsample",     value=float(gb.get("subsample",0.8)),          step=0.05, min_value=0.1, max_value=1.0, key="gb_sub")
    ts     = st.slider("Test set fraction", 0.1, 0.4, float(ms.get("test_split",0.2)), step=0.05)

    if st.button("💾 Apply Model Settings", type="primary", key="btn_ms"):
        cfg.setdefault("model_settings", {})
        cfg["model_settings"]["default_model"]                     = def_mdl
        cfg["model_settings"]["random_forest"]                     = {"n_estimators":int(rf_n),"max_depth":int(rf_d),"min_samples_leaf":int(rf_l)}
        cfg["model_settings"]["gradient_boosting"]                 = {"n_estimators":int(gb_n),"learning_rate":float(gb_lr),"max_depth":int(gb_d),"subsample":float(gb_sub)}
        cfg["model_settings"]["test_split"]                        = float(ts)
        save_config(cfg)
        st.success("✅ Model settings applied. Dashboard will retrain on next load.")


# ── TAB 5  POLICY SIMULATION ──────────────────────────────────────────────────
with t5:
    st.markdown('<div class="adm">📋 Policy Simulation Controls</div>', unsafe_allow_html=True)
    ps = cfg.get("policy_simulation", {})
    sr = ps.get("slider_ranges", {})

    st.markdown("#### Slider Ranges for Policy Levers")
    levers = [
        ("gdp_pct",       "💰 GDP per Capita Change (%)"),
        ("health_pct",    "🏥 Health Expenditure Change (%)"),
        ("fertility_pct", "👶 Fertility Rate Change (%)"),
        ("education_pct", "📚 Female Education Change (%)"),
    ]
    new_ranges = {}
    for key, label in levers:
        r = sr.get(key, {"min":-30,"max":60,"step":5})
        lc,mc2,hc = st.columns([3,1,1])
        lc.markdown(f"**{label}**")
        mn  = mc2.number_input(f"Min", value=int(r["min"]), step=5, key=f"mn_{key}")
        mx  = hc.number_input(f"Max",  value=int(r["max"]), step=5, key=f"mx_{key}")
        new_ranges[key] = {"min":mn, "max":mx, "step":r.get("step",5)}

    st.markdown("---")
    st.markdown("#### 🏛️ Government Scenario (one-click pre-load in Policy Simulation tab)")
    gs = ps.get("government_scenario", {})
    gs_name   = st.text_input("Scenario Name", value=gs.get("name","Ghana Health Sector Strategy 2030"))
    gsc1,gsc2,gsc3,gsc4 = st.columns(4)
    gs_gdp    = gsc1.number_input("GDP %",        value=int(gs.get("gdp_pct",15)),       step=5, key="gs_gdp")
    gs_health = gsc2.number_input("Health Exp %", value=int(gs.get("health_pct",40)),    step=5, key="gs_hlt")
    gs_fert   = gsc3.number_input("Fertility %",  value=int(gs.get("fertility_pct",-15)),step=5, key="gs_frt")
    gs_edu    = gsc4.number_input("Education %",  value=int(gs.get("education_pct",25)), step=5, key="gs_edu")
    show_btn  = st.checkbox("Show Government Scenario button on dashboard",
                            value=ps.get("show_gov_scenario_button", True))

    if st.button("💾 Apply Policy Simulation Settings", type="primary", key="btn_ps"):
        cfg.setdefault("policy_simulation", {})
        cfg["policy_simulation"]["slider_ranges"]                           = new_ranges
        cfg["policy_simulation"]["show_gov_scenario_button"]                = show_btn
        cfg["policy_simulation"]["government_scenario"]                     = {
            "name": gs_name, "gdp_pct": int(gs_gdp), "health_pct": int(gs_health),
            "fertility_pct": int(gs_fert), "education_pct": int(gs_edu)
        }
        save_config(cfg)
        st.success("✅ Policy simulation settings applied.")


# ── TAB 6  COUNTRY SETTINGS ───────────────────────────────────────────────────
with t6:
    st.markdown('<div class="adm">🌍 Country Settings</div>', unsafe_allow_html=True)
    cs = cfg.get("country_settings", {})

    new_default = st.text_input("Default Country on Load", value=cs.get("default_country","Ghana"))
    if st.button("💾 Set Default Country", key="btn_dc"):
        cfg.setdefault("country_settings", {})
        cfg["country_settings"]["default_country"] = new_default
        save_config(cfg)
        st.success(f"✅ Default country set to {new_default}.")

    # ── Policy recommendations ─────────────────────────────────────────────────
    st.markdown('<div class="adm">Policy Recommendations (per country)</div>', unsafe_allow_html=True)
    st.caption("Shown as an info box in the Country Analysis tab.")
    pr = cs.get("policy_recommendations", {})
    opts = list(pr.keys()) + ["➕ Add new country…"]
    sel  = st.selectbox("Country to edit", opts, key="pr_sel")
    if sel == "➕ Add new country…":
        sel = st.text_input("Country name (must match data exactly)", key="pr_new")
    if sel and sel != "➕ Add new country…":
        new_rec = st.text_area(f"Recommendation for {sel}", value=pr.get(sel,""), height=120)
        if st.button("💾 Save Recommendation", key="btn_rec"):
            cfg["country_settings"]["policy_recommendations"][sel] = new_rec
            save_config(cfg)
            st.success(f"✅ Recommendation for {sel} saved.")

    # ── Peer groups ────────────────────────────────────────────────────────────
    st.markdown('<div class="adm">Peer Comparison Groups</div>', unsafe_allow_html=True)
    st.caption("Comma-separated peer countries shown by default in Country Analysis.")
    pg       = cs.get("peer_groups", {})
    pg_keys  = list(pg.keys()) + ["➕ New group…"]
    pg_sel   = st.selectbox("Country to configure peers", pg_keys, key="pg_sel")
    if pg_sel == "➕ New group…":
        pg_sel = st.text_input("Country name", key="pg_new")
    if pg_sel and pg_sel != "➕ New group…":
        existing = ", ".join(pg.get(pg_sel, []))
        new_peers_raw = st.text_input(f"Peers for {pg_sel} (comma-separated)", value=existing)
        if st.button("💾 Save Peer Group", key="btn_pg"):
            cfg["country_settings"]["peer_groups"][pg_sel] = [p.strip() for p in new_peers_raw.split(",") if p.strip()]
            save_config(cfg)
            st.success(f"✅ Peer group for {pg_sel} saved.")

    # ── Timeline annotations ──────────────────────────────────────────────────
    st.markdown('<div class="adm">Timeline Annotations</div>', unsafe_allow_html=True)
    st.caption("Vertical dotted lines added to country MMR trend charts.")
    ta = cs.get("timeline_annotations", {})
    ann_cty = st.selectbox("Country", list(ta.keys()) + ["➕ New…"], key="ann_sel")
    if ann_cty == "➕ New…":
        ann_cty = st.text_input("Country name", key="ann_new")
    if ann_cty and ann_cty != "➕ New…":
        anns = ta.get(ann_cty, [])
        for i, ann in enumerate(anns):
            ac1,ac2,ac3,ac4 = st.columns([1,3,1,1])
            anns[i]["year"]  = ac1.number_input("Year",  value=int(ann["year"]),  key=f"ay{i}", min_value=1990, max_value=2030)
            anns[i]["label"] = ac2.text_input("Label", value=ann.get("label",""), key=f"al{i}")
            anns[i]["color"] = ac3.color_picker("Colour", value=ann.get("color","#009FD4"), key=f"ac{i}")
            if ac4.button("🗑️", key=f"del_{i}"):
                anns.pop(i)
                cfg["country_settings"]["timeline_annotations"][ann_cty] = anns
                save_config(cfg)
                st.rerun()
        if st.button("➕ Add annotation", key="btn_add_ann"):
            anns.append({"year":2024,"label":"New Event","color":"#009FD4"})
            cfg.setdefault("country_settings",{}).setdefault("timeline_annotations",{})[ann_cty] = anns
            save_config(cfg)
            st.rerun()


# ── TAB 7  SAVE & EXPORT ─────────────────────────────────────────────────────
with t7:
    st.markdown('<div class="adm">💾 Save, Export & Reset</div>', unsafe_allow_html=True)

    current = load_config()

    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown("#### ⬇️ Export current config")
        st.markdown("Download and commit to GitHub to make all changes permanent.")
        st.download_button("Download config.json",
                           data=json.dumps(current, indent=2, ensure_ascii=False),
                           file_name="config.json", mime="application/json",
                           use_container_width=True)
    with ec2:
        st.markdown("#### ⬆️ Import / restore config")
        uploaded = st.file_uploader("Upload config.json", type=["json"])
        if uploaded:
            try:
                restored = json.load(uploaded)
                st.json(restored)
                if st.button("✅ Apply uploaded config", type="primary", key="btn_restore"):
                    save_config(restored)
                    st.success("✅ Config restored. Switch to Dashboard tab.")
                    st.rerun()
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    st.markdown("---")
    st.markdown("#### 🔄 Reset to factory defaults")
    st.warning("This overwrites all settings with the original defaults.")
    DEFAULTS = {
        "branding": {
            "dashboard_title":    "MCH Policy Intelligence Dashboard",
            "dashboard_subtitle": "Maternal & Child Health · WHO / World Bank Data · Ministry of Health, Ghana",
            "footer_text":        "MCH Policy Intelligence Dashboard · Data: WHO / World Bank · Ministry of Health, Ghana · 2026",
            "show_tabs": {"global_overview":True,"country_analysis":True,"econometric_models":True,"xai_features":True,"policy_simulation":True}
        },
        "risk_thresholds": {
            "high_mmr":300,"medium_mmr":100,"low_mmr":50,
            "labels":{"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"},
            "colors":{"high":"#E63329","medium":"#F39200","low":"#009FD4","very_low":"#00A651"}
        },
        "who_benchmarks": {
            "sdg_mmr_target":70,"sdg_target_year":2030,
            "sdg_label":"SDG 3.1 Target (2030)",
            "min_health_expenditure_pct_gdp":5.0,
            "min_health_exp_label":"WHO Min. Health Exp. Threshold (5% GDP)",
            "show_benchmark_lines":True
        },
        "model_settings": {
            "default_model":"Random Forest",
            "random_forest":{"n_estimators":150,"max_depth":8,"min_samples_leaf":3},
            "gradient_boosting":{"n_estimators":150,"learning_rate":0.08,"max_depth":4,"subsample":0.8},
            "test_split":0.2,"random_state":42
        },
        "policy_simulation": {
            "slider_ranges":{
                "gdp_pct":{"min":-30,"max":60,"step":5},
                "health_pct":{"min":-30,"max":100,"step":5},
                "fertility_pct":{"min":-50,"max":20,"step":5},
                "education_pct":{"min":-20,"max":60,"step":5}
            },
            "government_scenario":{"name":"Ghana Health Sector Strategy 2030","gdp_pct":15,"health_pct":40,"fertility_pct":-15,"education_pct":25},
            "show_gov_scenario_button":True
        },
        "country_settings": {
            "default_country":"Ghana",
            "peer_groups":{"Ghana":["Nigeria","Kenya","Senegal","Cameroon"],"Kenya":["Ghana","Tanzania","Uganda","Ethiopia","Rwanda"]},
            "policy_recommendations":{
                "Ghana":"Priority: Increase skilled birth attendance. Expand CHPS to underserved rural zones. Target MMR < 70 by 2030 (SDG 3.1).",
                "Nigeria":"Priority: Strengthen primary healthcare infrastructure in the North. Accelerate female secondary education enrollment."
            },
            "timeline_annotations":{
                "Ghana":[{"year":2003,"label":"NHIS Established","color":"#009FD4"},{"year":2008,"label":"Free Maternal Care Policy","color":"#00A651"},{"year":2017,"label":"CHPS Revitalisation","color":"#F39200"}],
                "Kenya":[{"year":2013,"label":"Free Maternal Healthcare","color":"#00A651"},{"year":2018,"label":"UHC Pilot Begins","color":"#009FD4"}]
            }
        }
    }
    if st.button("🔄 Reset to defaults", type="secondary", key="btn_reset"):
        save_config(DEFAULTS)
        st.success("✅ Reset to factory defaults. Switch to Dashboard tab.")
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Current live config")
    st.json(current)

    if st.session_state.get("cfg_updated"):
        st.success("✅ Changes are live this session. Download config.json above and push to GitHub to persist permanently.")
