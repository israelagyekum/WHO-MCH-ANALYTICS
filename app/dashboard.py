"""
MCH Policy Intelligence Dashboard
Maternal & Child Health — WHO Data | Ministry of Health, Ghana
Config-driven: edit settings via the Admin Panel (pages/admin.py).
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
import matplotlib
matplotlib.use("Agg")
import shap
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.inspection import partial_dependence
import statsmodels.formula.api as smf
import statsmodels.api as sm

WHO_NAVY  = "#003F87"; WHO_BLUE  = "#009FD4"; WHO_GREEN = "#00A651"
WHO_RED   = "#E63329"; WHO_AMBER = "#F39200"; WHO_GRAY  = "#6D6E71"
WHO_LIGHT = "#EFF6FB"; WHO_WHITE = "#FFFFFF"
COLOR_SEQ = [WHO_NAVY,WHO_BLUE,WHO_GREEN,WHO_AMBER,WHO_RED,"#5C6BC0","#AB47BC"]

FEATURES = ["gdp_per_capita","fertility_rate",
            "health_expenditure_per_capita","female_secondary_enrollment"]
FEAT_LBL = {"gdp_per_capita":"GDP per Capita (USD)","fertility_rate":"Fertility Rate",
            "health_expenditure_per_capita":"Health Expenditure per Capita (USD)",
            "female_secondary_enrollment":"Female Secondary Enrollment (%)"}
TARGET = "maternal_mortality"

st.set_page_config(page_title="MCH Policy Dashboard — Ghana MoH",
                   page_icon="🏥", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""<style>
/* ── App background ── */
[data-testid="stAppViewContainer"]{{background-color:#F4F7FB;}}

/* ── Sidebar background ── */
[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,{WHO_NAVY} 0%,#002966 100%);
  padding-top:0.5rem;
}}

/* ── Sidebar labels & plain text ── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div.stMarkdown,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] small {{
  color:{WHO_WHITE} !important;
}}

/* ── Sidebar selectbox — dark input with white text ── */
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background:rgba(255,255,255,0.12) !important;
  border:1px solid rgba(255,255,255,0.25) !important;
  border-radius:6px !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] span {{
  color:{WHO_WHITE} !important;
}}

/* ── Sidebar radio buttons ── */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {{
  background:rgba(255,255,255,0.08);
  border-radius:6px; padding:4px 8px;
}}

/* ── Multipage navigation ── */
[data-testid="stSidebarNav"] {{
  background:rgba(0,0,0,0.15);
  border-radius:8px; padding:4px; margin-bottom:0.5rem;
}}
[data-testid="stSidebarNav"] a {{
  color:rgba(255,255,255,0.85) !important;
  border-radius:6px; padding:6px 12px;
  font-weight:600; font-size:0.88rem;
  display:block; text-decoration:none;
}}
[data-testid="stSidebarNav"] a:hover {{
  background:rgba(0,159,212,0.25) !important;
  color:{WHO_WHITE} !important;
}}
[data-testid="stSidebarNav"] [aria-selected="true"],
[data-testid="stSidebarNav"] a[aria-current="page"] {{
  background:{WHO_BLUE} !important;
  color:{WHO_WHITE} !important;
}}

/* ── Headers ── */
h1,h2,h3,h4{{color:{WHO_NAVY} !important;font-family:'Segoe UI',Arial,sans-serif !important;}}

/* ── Metric cards ── */
[data-testid="metric-container"]{{
  background:{WHO_WHITE};border:1px solid #D6E8F7;
  border-left:5px solid {WHO_BLUE};border-radius:8px;
  padding:0.75rem 1rem;box-shadow:0 2px 8px rgba(0,63,135,0.07);
}}
[data-testid="stMetricValue"]{{color:{WHO_NAVY} !important;font-weight:700;font-size:1.5rem !important;}}
[data-testid="stMetricLabel"]{{color:{WHO_GRAY} !important;font-size:0.75rem !important;text-transform:uppercase;}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{{
  gap:4px;background:{WHO_LIGHT};border-radius:10px 10px 0 0;padding:6px 6px 0;
}}
.stTabs [data-baseweb="tab"]{{
  background:transparent;color:{WHO_GRAY};border-radius:8px 8px 0 0;
  font-weight:600;font-size:0.85rem;padding:8px 18px;border:none;
}}
.stTabs [aria-selected="true"]{{
  background:{WHO_NAVY} !important;color:{WHO_WHITE} !important;
}}

/* ── Section headers ── */
.sec-hdr{{
  background:linear-gradient(90deg,{WHO_NAVY},{WHO_BLUE});color:white;
  padding:0.45rem 1rem;border-radius:6px;font-weight:700;font-size:0.95rem;
  margin:1.2rem 0 0.8rem;
}}

footer,#MainMenu{{display:none !important;visibility:hidden;}}
</style>""", unsafe_allow_html=True)


# ── Config helpers ────────────────────────────────────────────────────────────
def get_cfg():
    if st.session_state.get("cfg_updated") or "admin_cfg" not in st.session_state:
        try:
            with open(CONFIG_PATH) as f:
                st.session_state["admin_cfg"] = json.load(f)
        except Exception:
            st.session_state["admin_cfg"] = {}
        st.session_state["cfg_updated"] = False
    return st.session_state["admin_cfg"]

def risk_badge(mmr, cfg):
    rt   = cfg.get("risk_thresholds", {})
    clrs = rt.get("colors",  {"high":WHO_RED,"medium":WHO_AMBER,"low":WHO_BLUE,"very_low":WHO_GREEN})
    lbls = rt.get("labels",  {"high":"High Risk","medium":"Moderate Risk","low":"Low Risk","very_low":"On Track"})
    if   mmr > rt.get("high_mmr",   300): c,l = clrs["high"],     lbls["high"]
    elif mmr > rt.get("medium_mmr", 100): c,l = clrs["medium"],   lbls["medium"]
    elif mmr > rt.get("low_mmr",     50): c,l = clrs["low"],      lbls["low"]
    else:                                  c,l = clrs["very_low"], lbls["very_low"]
    return (f'<span style="background:{c};color:white;padding:2px 12px;'
            f'border-radius:12px;font-size:0.78rem;font-weight:700;">{l}</span>')

def add_sdg_line(fig, cfg):
    wb = cfg.get("who_benchmarks", {})
    if wb.get("show_benchmark_lines", True):
        fig.add_hline(y=wb.get("sdg_mmr_target",70), line_dash="dash",
                      line_color=WHO_GREEN, line_width=1.8,
                      annotation_text=wb.get("sdg_label","SDG 3.1 Target (2030)"),
                      annotation_font_color=WHO_GREEN, annotation_font_size=10)

def add_annotations(fig, country, cfg):
    ta = cfg.get("country_settings",{}).get("timeline_annotations",{})
    for ann in ta.get(country,[]):
        fig.add_vline(x=ann["year"], line_dash="dot",
                      line_color=ann.get("color",WHO_BLUE), line_width=1.5,
                      annotation_text=ann.get("label",""),
                      annotation_font_size=9,
                      annotation_font_color=ann.get("color",WHO_BLUE))


# ── Data & models ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=FEATURES+[TARGET])
    df["log_mmr"]        = np.log(df[TARGET].clip(lower=1))
    df["log_gdp"]        = np.log(df["gdp_per_capita"].clip(lower=1))
    df["log_health_exp"] = np.log(df["health_expenditure_per_capita"].clip(lower=1))
    return df

@st.cache_resource(show_spinner=False)
def train_models(_n, _rf, _gb, _ts):
    rfp = json.loads(_rf); gbp = json.loads(_gb)
    df  = load_data()
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
def run_econometrics(_n):
    df  = load_data()
    ols = sm.OLS(df["log_mmr"], sm.add_constant(df[["log_gdp","log_health_exp",
                  "fertility_rate","female_secondary_enrollment"]])).fit(cov_type="HC3")
    fe  = smf.ols("log_mmr ~ log_gdp + log_health_exp + fertility_rate"
                  " + female_secondary_enrollment + C(country) + C(year)",
                  data=df).fit(cov_type="cluster",cov_kwds={"groups":df["country"]})
    return ols, fe

# ── Bootstrap ─────────────────────────────────────────────────────────────────
with st.spinner("Loading WHO dataset…"):
    df  = load_data()
    cfg = get_cfg()

ms  = cfg.get("model_settings",{})
rfc = json.dumps(ms.get("random_forest",{"n_estimators":150,"max_depth":8,"min_samples_leaf":3}),sort_keys=True)
gbc = json.dumps(ms.get("gradient_boosting",{"n_estimators":150,"learning_rate":0.08,"max_depth":4,"subsample":0.8}),sort_keys=True)
with st.spinner("Initialising models…"):
    models = train_models(len(df),rfc,gbc,ms.get("test_split",0.2))

# ── Masthead ──────────────────────────────────────────────────────────────────
br      = cfg.get("branding",{})
T       = br.get("dashboard_title","MCH Policy Intelligence Dashboard")
S       = br.get("dashboard_subtitle","Maternal & Child Health — WHO Data | Ministry of Health, Ghana")
FOOT    = br.get("footer_text","MCH Policy Intelligence Dashboard · WHO / World Bank · Ministry of Health, Ghana · 2026")

st.markdown(f"""
<div style="background:linear-gradient(135deg,{WHO_NAVY} 0%,{WHO_BLUE} 100%);
            padding:1.4rem 2rem;border-radius:12px;margin-bottom:1.2rem;
            box-shadow:0 4px 20px rgba(0,63,135,0.25);">
  <div style="color:white;font-size:1.65rem;font-weight:800;font-family:'Segoe UI',Arial,sans-serif;">
    🏥 &nbsp;{T}
  </div>
  <div style="color:rgba(255,255,255,0.82);font-size:0.9rem;margin-top:0.35rem;">{S}</div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 Dashboard Controls")
    st.markdown("---")
    cs_cfg   = cfg.get("country_settings",{})
    def_cty  = cs_cfg.get("default_country","Ghana")
    all_cty  = sorted(df["country"].unique())
    def_idx  = all_cty.index(def_cty) if def_cty in all_cty else 0
    country  = st.selectbox("📍 Country", all_cty, index=def_idx)
    all_yrs  = sorted(df["year"].unique())
    year     = st.selectbox("📅 Reference Year", all_yrs, index=len(all_yrs)-1)
    st.markdown("---")
    def_mdl  = ms.get("default_model","Random Forest")
    mc       = st.radio("🤖 Active ML Model",["Random Forest","Gradient Boosting"],
                        index=0 if def_mdl=="Random Forest" else 1)
    st.markdown("---")
    st.markdown(f"<div style='font-size:0.8rem;line-height:1.9;'>"
                f"<b>Data:</b> WHO / World Bank<br><b>Countries:</b> {df['country'].nunique()}<br>"
                f"<b>Period:</b> {df['year'].min()}–{df['year'].max()}<br>"
                f"<b>Observations:</b> {len(df):,}</div>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size:0.72rem;color:rgba(255,255,255,0.5);text-align:center;'>"
                "Ministry of Health, Ghana<br>MPhil Data Science · 2026</div>",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        f"""<a href="/admin" target="_self"
            style="display:block;background:rgba(0,159,212,0.25);color:white;
                   text-align:center;padding:8px;border-radius:8px;
                   border:1px solid rgba(0,159,212,0.5);font-weight:700;
                   font-size:0.85rem;text-decoration:none;margin-top:4px;">
            ⚙️ &nbsp;Admin Panel
        </a>""",
        unsafe_allow_html=True)

# ── Derived ───────────────────────────────────────────────────────────────────
am  = models["rf"] if mc=="Random Forest" else models["gb"]
amm = models["rf_metrics"] if mc=="Random Forest" else models["gb_metrics"]
cdf = df[df["country"]==country]
rdf = cdf[cdf["year"]==year]
if rdf.empty: rdf = cdf.sort_values("year").iloc[[-1]]
row = rdf.iloc[0]

_L  = dict(plot_bgcolor=WHO_WHITE,paper_bgcolor=WHO_WHITE,
           font=dict(family="Segoe UI,Arial",size=12,color="#2D3748"),
           title_font=dict(size=13,color=WHO_NAVY),margin=dict(t=50,b=40,l=40,r=20))

show_tabs = br.get("show_tabs",{})
tab_defs  = [("global_overview","🌍  Global Overview"),
             ("country_analysis","🔬  Country Analysis"),
             ("econometric_models","📊  Econometric Models"),
             ("xai_features","🤖  XAI & Feature Analysis"),
             ("policy_simulation","🎯  Policy Simulation")]
vis_lbls  = [l for k,l in tab_defs if show_tabs.get(k,True)]
tabs_list = st.tabs(vis_lbls)
tm        = {k:tabs_list[i] for i,(k,_) in enumerate((kl for kl in tab_defs if show_tabs.get(kl[0],True)))}


# ══════════════════════════════════════════════════════════
# TAB 1  GLOBAL OVERVIEW
# ══════════════════════════════════════════════════════════
if "global_overview" in tm:
 with tm["global_overview"]:
  st.markdown('<div class="sec-hdr">🌍 Global Maternal Mortality Overview</div>',unsafe_allow_html=True)
  lat = df.sort_values("year").groupby("country",as_index=False).last()
  k1,k2,k3,k4,k5=st.columns(5)
  k1.metric("Countries Tracked",f"{df['country'].nunique()}")
  k2.metric("Global Avg MMR",f"{lat[TARGET].mean():.0f}",help="per 100,000 live births")
  k3.metric("Avg Health Exp.",f"${lat['health_expenditure_per_capita'].mean():.0f}")
  k4.metric("Avg Fertility Rate",f"{lat['fertility_rate'].mean():.2f}")
  k5.metric("Avg Female Education",f"{lat['female_secondary_enrollment'].mean():.1f}%")
  st.markdown("---")
  cm,ct=st.columns([3,2])
  with cm:
   fig_map=px.choropleth(lat,locations="country",locationmode="country names",color=TARGET,
                          title="Maternal Mortality Rate — Latest Available Year",
                          color_continuous_scale=["#EFF6FB",WHO_BLUE,WHO_NAVY,WHO_RED],
                          labels={TARGET:"MMR per 100k"})
   fig_map.update_layout(**_L,geo=dict(showframe=False,showcoastlines=True,
                          projection_type="natural earth",bgcolor=WHO_WHITE),
                          coloraxis_colorbar=dict(title="MMR<br>per 100k",title_font=dict(size=11)))
   st.plotly_chart(fig_map,use_container_width=True)
  with ct:
   t10=lat.nlargest(10,TARGET)[["country",TARGET]].reset_index(drop=True)
   fig_top=px.bar(t10,x=TARGET,y="country",orientation="h",title="Top 10 Highest MMR Countries",
                   color=TARGET,color_continuous_scale=[WHO_AMBER,WHO_RED],
                   labels={TARGET:"MMR per 100k","country":""})
   fig_top.update_layout(**_L,showlegend=False,yaxis=dict(autorange="reversed"),coloraxis_showscale=False)
   st.plotly_chart(fig_top,use_container_width=True)
  gt=df.groupby("year")[TARGET].mean().reset_index()
  fig_gt=px.line(gt,x="year",y=TARGET,title="Global Average MMR Trend",
                  color_discrete_sequence=[WHO_BLUE],labels={TARGET:"MMR per 100k","year":"Year"})
  fig_gt.update_traces(line_width=3)
  add_sdg_line(fig_gt,cfg)
  fig_gt.update_layout(**_L,xaxis=dict(gridcolor="#E8EFF8"),yaxis=dict(gridcolor="#E8EFF8"))
  st.plotly_chart(fig_gt,use_container_width=True)
  st.markdown('<div class="sec-hdr">Key Correlations — All Countries</div>',unsafe_allow_html=True)
  fig_sc=px.scatter(lat,x="gdp_per_capita",y=TARGET,size="health_expenditure_per_capita",
                     color="fertility_rate",hover_name="country",log_x=True,
                     color_continuous_scale=[WHO_GREEN,WHO_AMBER,WHO_RED],
                     title="GDP per Capita vs MMR  (bubble = health spending · colour = fertility)",
                     labels={"gdp_per_capita":"GDP per Capita (USD, log scale)",
                             TARGET:"MMR per 100k","fertility_rate":"Fertility Rate"})
  fig_sc.update_layout(**_L)
  st.plotly_chart(fig_sc,use_container_width=True)


# ══════════════════════════════════════════════════════════
# TAB 2  COUNTRY ANALYSIS
# ══════════════════════════════════════════════════════════
if "country_analysis" in tm:
 with tm["country_analysis"]:
  st.markdown(f'<div class="sec-hdr">🔬 Country Deep Dive — {country}</div>',unsafe_allow_html=True)
  c1,c2,c3,c4,c5=st.columns(5)
  c1.metric("Maternal Mortality",f"{row[TARGET]:.0f}",help="per 100,000 live births")
  c2.metric("GDP per Capita",f"${row['gdp_per_capita']:,.0f}")
  c3.metric("Health Expenditure",f"${row['health_expenditure_per_capita']:,.0f}")
  c4.metric("Fertility Rate",f"{row['fertility_rate']:.2f}")
  c5.metric("Female Education",f"{row['female_secondary_enrollment']:.1f}%")
  st.markdown(f"<div style='margin:-0.4rem 0 1rem;'>Risk Level: &nbsp;{risk_badge(row[TARGET],cfg)}</div>",
              unsafe_allow_html=True)
  pr  = cs_cfg.get("policy_recommendations",{})
  rec = pr.get(country,"")
  if rec:
      st.info(f"**🏛️ Policy Recommendation — {country}**\n\n{rec}")
  st.markdown("---")
  ca,cb=st.columns(2)
  with ca:
   fig_a=px.area(cdf.sort_values("year"),x="year",y=TARGET,
                  title=f"Maternal Mortality Trend — {country}",
                  labels={TARGET:"MMR per 100k","year":"Year"},
                  color_discrete_sequence=[WHO_BLUE])
   fig_a.update_traces(fillcolor="rgba(0,159,212,0.12)",line_color=WHO_BLUE,line_width=2.5)
   add_sdg_line(fig_a,cfg); add_annotations(fig_a,country,cfg)
   fig_a.update_layout(**_L)
   st.plotly_chart(fig_a,use_container_width=True)
  with cb:
   fig_b=px.line(cdf.sort_values("year"),x="year",y="health_expenditure_per_capita",
                  title=f"Health Expenditure Trend — {country}",
                  labels={"health_expenditure_per_capita":"USD per capita","year":"Year"},
                  color_discrete_sequence=[WHO_GREEN])
   fig_b.update_traces(line_width=2.5)
   add_annotations(fig_b,country,cfg)
   fig_b.update_layout(**_L)
   st.plotly_chart(fig_b,use_container_width=True)
  st.markdown('<div class="sec-hdr">Regional / Peer Comparison</div>',unsafe_allow_html=True)
  pg          = cs_cfg.get("peer_groups",{})
  cfg_peers   = [c for c in pg.get(country,[]) if c in df["country"].unique()][:4]
  def_peers   = ([country]+cfg_peers) if country not in cfg_peers else cfg_peers
  comp_sel    = st.multiselect("Countries to compare",all_cty,default=def_peers[:5])
  if comp_sel:
   fig_cp=px.line(df[df["country"].isin(comp_sel)].sort_values("year"),x="year",y=TARGET,
                   color="country",title="MMR Comparison — Selected Countries",
                   color_discrete_sequence=COLOR_SEQ,
                   labels={TARGET:"MMR per 100k","year":"Year"})
   for tr in fig_cp.data:
       if tr.name==country: tr.line.width=4; tr.line.color=WHO_RED
   add_sdg_line(fig_cp,cfg)
   fig_cp.update_layout(**_L)
   st.plotly_chart(fig_cp,use_container_width=True)
  ydf=df[df["year"]==year].copy()
  fig_s2=px.scatter(ydf,x="gdp_per_capita",y=TARGET,hover_name="country",
                     size="health_expenditure_per_capita",color="fertility_rate",log_x=True,
                     color_continuous_scale=[WHO_GREEN,WHO_AMBER,WHO_RED],
                     title=f"GDP per Capita vs MMR ({year}) — {country} starred",
                     labels={"gdp_per_capita":"GDP per Capita (USD, log scale)",
                             TARGET:"MMR per 100k","fertility_rate":"Fertility Rate"})
  if not rdf.empty:
      fig_s2.add_scatter(x=[row["gdp_per_capita"]],y=[row[TARGET]],
                         mode="markers+text",text=[f"  {country}"],textposition="middle right",
                         marker=dict(color=WHO_RED,size=16,symbol="star",
                                     line=dict(color=WHO_NAVY,width=2)),showlegend=False)
  fig_s2.update_layout(**_L)
  st.plotly_chart(fig_s2,use_container_width=True)


# ══════════════════════════════════════════════════════════
# TAB 3  ECONOMETRIC MODELS
# ══════════════════════════════════════════════════════════
if "econometric_models" in tm:
 with tm["econometric_models"]:
  st.markdown('<div class="sec-hdr">📊 Panel Econometric Analysis</div>',unsafe_allow_html=True)
  with st.spinner("Running regressions…"):
      ols_m,fe_m=run_econometrics(len(df))
  CV=["log_gdp","log_health_exp","fertility_rate","female_secondary_enrollment"]
  CL=["log(GDP p.c.)","log(Health Exp.)","Fertility Rate","Female Education"]
  def sig(p): return "***" if p<0.01 else "**" if p<0.05 else "*" if p<0.1 else ""
  co,cf=st.columns(2)
  with co:
   st.markdown("#### Pooled OLS — Log-Log Specification")
   st.caption("Dep. var: ln(MMR)  |  Robust SE (HC3)")
   ro=[{"Variable":l,"Coef.":round(ols_m.params[v],4),"Std Err":round(ols_m.bse[v],4),
        "t":round(ols_m.tvalues[v],3),"p":round(ols_m.pvalues[v],4),"Sig.":sig(ols_m.pvalues[v])}
       for v,l in zip(CV,CL) if v in ols_m.params.index]
   st.dataframe(pd.DataFrame(ro),use_container_width=True,hide_index=True)
   st.dataframe(pd.DataFrame({"Metric":["R²","Adj. R²","F-stat","N"],
       "Value":[f"{ols_m.rsquared:.4f}",f"{ols_m.rsquared_adj:.4f}",
                f"{ols_m.fvalue:.2f}",f"{int(ols_m.nobs):,}"]}),
       use_container_width=True,hide_index=True)
   st.caption("*** p<0.01  ** p<0.05  * p<0.1")
  with cf:
   st.markdown("#### Two-Way Fixed Effects")
   st.caption("Country FE + Year FE  |  Clustered SE by country")
   rf2=[{"Variable":l,"Coef.":round(fe_m.params[v],4),"Std Err":round(fe_m.bse[v],4),
         "t":round(fe_m.tvalues[v],3),"p":round(fe_m.pvalues[v],4),"Sig.":sig(fe_m.pvalues[v])}
        for v,l in zip(CV,CL) if v in fe_m.params.index]
   st.dataframe(pd.DataFrame(rf2),use_container_width=True,hide_index=True)
   st.dataframe(pd.DataFrame({"Metric":["Within R²","F-stat","N","Countries","Years"],
       "Value":[f"{fe_m.rsquared:.4f}",f"{fe_m.fvalue:.2f}",
                f"{int(fe_m.nobs):,}",f"{df['country'].nunique()}",f"{df['year'].nunique()}"]}),
       use_container_width=True,hide_index=True)
   st.caption("*** p<0.01  ** p<0.05  * p<0.1")
  st.markdown('<div class="sec-hdr">Coefficient Plot — OLS vs Fixed Effects (95% CI)</div>',unsafe_allow_html=True)
  crow=[]
  for v,l in zip(CV,CL):
   for mdl,mn in [(ols_m,"Pooled OLS"),(fe_m,"Fixed Effects")]:
    if v in mdl.params.index:
     ci=mdl.conf_int().loc[v]
     crow.append(dict(Model=mn,Variable=l,Coef=mdl.params[v],CI_lo=ci[0],CI_hi=ci[1]))
  cdf2=pd.DataFrame(crow)
  fig_c=go.Figure()
  for mn,cl in [("Pooled OLS",WHO_BLUE),("Fixed Effects",WHO_NAVY)]:
   s=cdf2[cdf2["Model"]==mn]
   fig_c.add_trace(go.Scatter(x=s["Variable"],y=s["Coef"],
    error_y=dict(type="data",symmetric=False,array=s["CI_hi"]-s["Coef"],
                 arrayminus=s["Coef"]-s["CI_lo"],thickness=2,width=6),
    mode="markers",marker=dict(size=11,color=cl,line=dict(color=WHO_WHITE,width=1.5)),name=mn))
  fig_c.add_hline(y=0,line_dash="dash",line_color=WHO_GRAY,line_width=1.2)
  fig_c.update_layout(**_L,title="Coefficient Estimates with 95% CI",
                      xaxis_title="Variable",yaxis_title="Coefficient on ln(MMR)",
                      legend=dict(orientation="h",yanchor="bottom",y=1.02))
  st.plotly_chart(fig_c,use_container_width=True)
  go_=ols_m.params.get("log_gdp",0); gf_=fe_m.params.get("log_gdp",0)
  ho_=ols_m.params.get("log_health_exp",0); hf_=fe_m.params.get("log_health_exp",0)
  ff_=fe_m.params.get("fertility_rate",0); ef_=fe_m.params.get("female_secondary_enrollment",0)
  st.markdown('<div class="sec-hdr">Economic Interpretation</div>',unsafe_allow_html=True)
  st.info(f"""
**Key Findings from the Panel Analysis**

**GDP per Capita** — A 1% rise is associated with a **{abs(go_):.2f}% {'decrease' if go_<0 else 'increase'}** in MMR (Pooled OLS) and **{abs(gf_):.2f}% {'decrease' if gf_<0 else 'increase'}** after country + year fixed effects.

**Health Expenditure** — A 1% rise in per-capita spending is associated with a **{abs(ho_):.2f}% {'decrease' if ho_<0 else 'increase'}** in MMR (OLS) vs **{abs(hf_):.2f}% {'decrease' if hf_<0 else 'increase'}** (FE).

**Fertility Rate** — Each unit rise is associated with a **{abs(ff_):.3f} {'decrease' if ff_<0 else 'increase'}** in ln(MMR) under Fixed Effects.

**Female Education** — Each 1 pp increase is associated with a **{abs(ef_):.4f} {'decrease' if ef_<0 else 'increase'}** in ln(MMR).

> Two-way fixed effects remove unobserved country heterogeneity and global time shocks, yielding cleaner causal policy estimates than pooled OLS.
""")


# ══════════════════════════════════════════════════════════
# TAB 4  XAI & FEATURE ANALYSIS
# ══════════════════════════════════════════════════════════
if "xai_features" in tm:
 with tm["xai_features"]:
  st.markdown('<div class="sec-hdr">🤖 Explainable AI — Model Interpretability</div>',unsafe_allow_html=True)
  m1,m2,m3,m4=st.columns(4)
  m1.metric("Active Model",mc); m2.metric("R² (test)",f"{amm['r2']:.4f}")
  m3.metric("RMSE",f"{amm['rmse']:.2f}"); m4.metric("MAE",f"{amm['mae']:.2f}")
  st.markdown("#### Model Comparison")
  st.dataframe(pd.DataFrame({"Model":["Random Forest","Gradient Boosting"],
      "R²":[models["rf_metrics"]["r2"],models["gb_metrics"]["r2"]],
      "RMSE":[models["rf_metrics"]["rmse"],models["gb_metrics"]["rmse"]],
      "MAE":[models["rf_metrics"]["mae"],models["gb_metrics"]["mae"]]}).round(4),
      use_container_width=True,hide_index=True)
  st.markdown("---")
  cfi,csh=st.columns(2)
  with cfi:
   st.markdown("#### Feature Importance (Gini Impurity)")
   fi=pd.DataFrame({"Feature":[FEAT_LBL[f] for f in FEATURES],
                    "Importance":am.feature_importances_}).sort_values("Importance")
   fig_fi=go.Figure(go.Bar(x=fi["Importance"],y=fi["Feature"],orientation="h",
       marker=dict(color=fi["Importance"],
                   colorscale=[[0,WHO_LIGHT],[0.5,WHO_BLUE],[1,WHO_NAVY]],showscale=False),
       text=[f"{v:.3f}" for v in fi["Importance"]],textposition="outside"))
   fig_fi.update_layout(**_L,title="Feature Importance",xaxis_title="Importance Score")
   st.plotly_chart(fig_fi,use_container_width=True)
  with csh:
   st.markdown("#### SHAP — Mean Absolute Impact")
   try:
    exp=shap.TreeExplainer(models["rf"])
    sv =exp.shap_values(models["X_test"])
    ms2=np.abs(sv).mean(axis=0)
    shdf=pd.DataFrame({"Feature":[FEAT_LBL[f] for f in FEATURES],"Mean |SHAP|":ms2}).sort_values("Mean |SHAP|")
    fig_sh=go.Figure(go.Bar(x=shdf["Mean |SHAP|"],y=shdf["Feature"],orientation="h",
        marker_color=WHO_BLUE,text=[f"{v:.1f}" for v in shdf["Mean |SHAP|"]],textposition="outside"))
    fig_sh.update_layout(**_L,title="Mean |SHAP| — Random Forest",xaxis_title="Mean |SHAP Value|")
    st.plotly_chart(fig_sh,use_container_width=True)
   except Exception as e:
    st.warning(f"SHAP error: {e}")
  st.markdown(f'<div class="sec-hdr">SHAP Waterfall — {country} ({year})</div>',unsafe_allow_html=True)
  try:
   exp=shap.TreeExplainer(models["rf"])
   rf_=pd.DataFrame([{f:row[f] for f in FEATURES}])
   sr_=exp.shap_values(rf_)[0]
   wf=pd.DataFrame({"Feature":[FEAT_LBL[f] for f in FEATURES],
                    "SHAP Value":sr_,"Feature Value":[row[f] for f in FEATURES]}).sort_values("SHAP Value")
   fig_wf=go.Figure(go.Bar(x=wf["SHAP Value"],y=wf["Feature"],orientation="h",
       marker_color=[WHO_GREEN if v<0 else WHO_RED for v in wf["SHAP Value"]],
       text=[f"val={v:.2f}" for v in wf["Feature Value"]],textposition="outside"))
   fig_wf.add_vline(x=0,line_color=WHO_GRAY,line_dash="dash",line_width=1.2)
   fig_wf.update_layout(**_L,title=f"SHAP Contributions — {country}",
                        xaxis_title="SHAP Value (impact on predicted MMR)")
   st.plotly_chart(fig_wf,use_container_width=True)
   st.caption(f"🟢 Green = reduces MMR  ·  🔴 Red = increases MMR  ·  Baseline = {exp.expected_value:.1f}")
  except Exception as e:
   st.warning(f"SHAP waterfall: {e}")
  st.markdown('<div class="sec-hdr">Partial Dependence Plot</div>',unsafe_allow_html=True)
  pf=st.selectbox("Select feature",FEATURES,format_func=lambda x:FEAT_LBL[x])
  try:
   pr2=partial_dependence(models["rf"],models["X_test"],features=[FEATURES.index(pf)],grid_resolution=60)
   pdd=pd.DataFrame({"Feature Value":pr2["grid_values"][0],"Predicted MMR":pr2["average"][0]})
   fig_pd=px.line(pdd,x="Feature Value",y="Predicted MMR",
                   title=f"Partial Dependence — {FEAT_LBL[pf]}",color_discrete_sequence=[WHO_NAVY],
                   labels={"Feature Value":FEAT_LBL[pf]})
   fig_pd.update_traces(line_width=3)
   fig_pd.add_vline(x=row[pf],line_dash="dot",line_color=WHO_RED,line_width=2,
                    annotation_text=f"{country}",annotation_font_color=WHO_RED)
   fig_pd.update_layout(**_L)
   st.plotly_chart(fig_pd,use_container_width=True)
   st.caption(f"Red dashed line = current value for {country} ({year})")
  except Exception as e:
   st.warning(f"PDP: {e}")


# ══════════════════════════════════════════════════════════
# TAB 5  POLICY SIMULATION
# ══════════════════════════════════════════════════════════
if "policy_simulation" in tm:
 with tm["policy_simulation"]:
  st.markdown(f'<div class="sec-hdr">🎯 Policy Simulation — {country} · {year}</div>',unsafe_allow_html=True)
  st.markdown("Adjust policy levers to project the impact on Maternal Mortality Rate in real time.")
  psc=cfg.get("policy_simulation",{}); sr2=psc.get("slider_ranges",{})
  gr2=sr2.get("gdp_pct",{"min":-30,"max":60,"step":5})
  hr2=sr2.get("health_pct",{"min":-30,"max":100,"step":5})
  fr2=sr2.get("fertility_pct",{"min":-50,"max":20,"step":5})
  er2=sr2.get("education_pct",{"min":-20,"max":60,"step":5})
  gs2=psc.get("government_scenario",{})
  if psc.get("show_gov_scenario_button",True) and gs2:
   if st.button(f"🏛️ Load: {gs2.get('name','Government Scenario')}",type="secondary"):
    st.session_state["sim_gdp"]=gs2.get("gdp_pct",0)
    st.session_state["sim_health"]=gs2.get("health_pct",0)
    st.session_state["sim_fert"]=gs2.get("fertility_pct",0)
    st.session_state["sim_edu"]=gs2.get("education_pct",0)
  sl1,sl2=st.columns(2)
  with sl1:
   gp=st.slider("💰 GDP per Capita Change (%)",gr2["min"],gr2["max"],
                st.session_state.get("sim_gdp",0),step=gr2["step"])
   hp=st.slider("🏥 Health Expenditure Change (%)",hr2["min"],hr2["max"],
                st.session_state.get("sim_health",0),step=hr2["step"])
  with sl2:
   fp=st.slider("👶 Fertility Rate Change (%)",fr2["min"],fr2["max"],
                st.session_state.get("sim_fert",0),step=fr2["step"])
   ep=st.slider("📚 Female Enrolment Change (%)",er2["min"],er2["max"],
                st.session_state.get("sim_edu",0),step=er2["step"])
  sn=st.text_input("📋 Scenario Name","Custom Policy Scenario")
  bv={f:row[f] for f in FEATURES}
  sv2={"gdp_per_capita":row["gdp_per_capita"]*(1+gp/100),
       "fertility_rate":row["fertility_rate"]*(1+fp/100),
       "health_expenditure_per_capita":row["health_expenditure_per_capita"]*(1+hp/100),
       "female_secondary_enrollment":row["female_secondary_enrollment"]*(1+ep/100)}
  bp=am.predict(pd.DataFrame([bv])[FEATURES])[0]
  sp=am.predict(pd.DataFrame([sv2])[FEATURES])[0]
  da=bp-sp; dp=(sp-bp)/bp*100
  sdg=cfg.get("who_benchmarks",{}).get("sdg_mmr_target",70)
  st.markdown("---"); st.markdown("### Simulation Results")
  r1,r2,r3,r4=st.columns(4)
  r1.metric("Baseline MMR",f"{bp:.1f}")
  r2.metric("Projected MMR",f"{sp:.1f}",delta=f"{dp:+.1f}%",delta_color="inverse")
  r3.metric("MMR Change /100k",f"{da:+.1f}",delta_color="inverse")
  r4.metric(f"vs SDG Target ({sdg:.0f})",f"{sp-sdg:+.1f}",delta_color="inverse")
  vz1,vz2=st.columns(2)
  with vz1:
   bc=WHO_GREEN if sp<bp else WHO_RED
   fig_sm=go.Figure(go.Bar(x=["Baseline",sn],y=[bp,sp],marker_color=[WHO_BLUE,bc],
                            text=[f"{bp:.1f}",f"{sp:.1f}"],textposition="outside",width=0.45))
   fig_sm.add_hline(y=bp,line_dash="dot",line_color=WHO_GRAY,line_width=1.5)
   add_sdg_line(fig_sm,cfg)
   fig_sm.update_layout(**_L,title="Baseline vs Policy Scenario",
                        yaxis_title="MMR per 100,000 live births",
                        yaxis_range=[0,max(bp,sp)*1.25])
   st.plotly_chart(fig_sm,use_container_width=True)
  with vz2:
   tr2=[]
   for lb,cl,pc in [("💰 GDP","gdp_per_capita",gp),
                    ("🏥 Health Spending","health_expenditure_per_capita",hp),
                    ("👶 Fertility Rate","fertility_rate",fp),
                    ("📚 Female Education","female_secondary_enrollment",ep)]:
    if pc!=0:
     tmp=pd.DataFrame([bv])[FEATURES].copy()
     tmp[cl]=row[cl]*(1+pc/100)
     tr2.append({"Lever":lb,"Impact":bp-am.predict(tmp)[0]})
   if tr2:
    tdf2=pd.DataFrame(tr2).sort_values("Impact")
    fig_t=go.Figure(go.Bar(x=tdf2["Impact"],y=tdf2["Lever"],orientation="h",
        marker_color=[WHO_GREEN if v>0 else WHO_RED for v in tdf2["Impact"]],
        text=[f"{v:+.1f}" for v in tdf2["Impact"]],textposition="outside"))
    fig_t.add_vline(x=0,line_dash="dash",line_color=WHO_GRAY,line_width=1)
    fig_t.update_layout(**_L,title="Individual Lever Contributions",
                        xaxis_title="MMR reduction (positive = fewer deaths)")
    st.plotly_chart(fig_t,use_container_width=True)
   else:
    st.info("Adjust at least one lever to see the tornado chart.")
  st.markdown('<div class="sec-hdr">Policy Input Summary</div>',unsafe_allow_html=True)
  st.dataframe(pd.DataFrame({
      "Indicator":["GDP per Capita (USD)","Health Expenditure (USD)","Fertility Rate","Female Education (%)"],
      "Baseline":[f"${bv['gdp_per_capita']:,.0f}",f"${bv['health_expenditure_per_capita']:,.0f}",
                  f"{bv['fertility_rate']:.2f}",f"{bv['female_secondary_enrollment']:.1f}%"],
      "Policy Scenario":[f"${sv2['gdp_per_capita']:,.0f}  ({gp:+d}%)",
                         f"${sv2['health_expenditure_per_capita']:,.0f}  ({hp:+d}%)",
                         f"{sv2['fertility_rate']:.2f}  ({fp:+d}%)",
                         f"{sv2['female_secondary_enrollment']:.1f}%  ({ep:+d}%)"]}),
      use_container_width=True,hide_index=True)
  st.caption(f"Model: {mc}  ·  Country: {country}  ·  Reference year: {year}")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""<div style="text-align:center;color:{WHO_GRAY};font-size:0.8rem;padding:0.4rem 0 1rem;">
  {FOOT}<br>
  <span style="color:{WHO_BLUE};">Explainable AI (SHAP) &nbsp;·&nbsp; Panel Econometrics (Two-Way Fixed Effects) &nbsp;·&nbsp; ML Policy Simulation</span>
</div>""", unsafe_allow_html=True)
