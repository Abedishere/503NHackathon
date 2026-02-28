import streamlit as st
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Conut EDA Dashboard", layout="wide")

EDA_ROOT = Path(__file__).resolve().parents[1]
TABLES = EDA_ROOT / "outputs" / "tables"
FIGS = EDA_ROOT / "outputs" / "figures"

@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    p = TABLES / name
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)

st.title("Conut – Advanced EDA Dashboard")
st.caption("Reads from outputs/tables and outputs/figures. Run pipeline if some data is missing.")

kpis = load_csv("branch_kpis.csv")
growth = load_csv("growth_metrics_all_branches.csv")
pairs_all = load_csv("combo_pairs_scored_all_branches.csv")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Branch KPIs")
    if kpis.empty:
        st.warning("branch_kpis.csv not found yet. Run: python -m eda.scripts.run_eda")
    else:
        st.dataframe(kpis, use_container_width=True)

with col2:
    st.subheader("Growth Metrics")
    if growth.empty:
        st.warning("growth_metrics_all_branches.csv not found yet.")
    else:
        st.dataframe(growth, use_container_width=True)

with col3:
    st.subheader("Top Combo Signals")
    if pairs_all.empty:
        st.warning("combo_pairs_scored_all_branches.csv not found yet.")
    else:
        st.dataframe(pairs_all.head(30), use_container_width=True)

st.divider()
st.subheader("Saved Figures")
if FIGS.exists():
    imgs = sorted([p for p in FIGS.glob("*.png")])
    if not imgs:
        st.info("No figures found yet.")
    else:
        for p in imgs[:12]:
            st.image(str(p), caption=p.name, use_column_width=True)