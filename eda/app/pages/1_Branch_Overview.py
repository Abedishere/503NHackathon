import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px

EDA_ROOT = Path(__file__).resolve().parents[2]
TABLES = EDA_ROOT / "outputs" / "tables"

@st.cache_data
def load(name: str) -> pd.DataFrame:
    p = TABLES / name
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)

st.title("Branch Overview")

kpis = load("branch_kpis.csv")
monthly = load("monthly_sales_clean.csv")

if kpis.empty:
    st.warning("Missing branch_kpis.csv – run pipeline.")
    st.stop()

branches = ["All"] + sorted(kpis["branch"].dropna().unique().tolist())
branch = st.sidebar.selectbox("Branch", branches)

view = kpis if branch == "All" else kpis[kpis["branch"] == branch]
st.dataframe(view, use_container_width=True)

if not monthly.empty and {"branch","period","sales"}.issubset(monthly.columns):
    monthly["period"] = pd.to_datetime(monthly["period"], errors="coerce")
    monthly["sales"] = pd.to_numeric(monthly["sales"], errors="coerce")

    m = monthly if branch == "All" else monthly[monthly["branch"] == branch]
    fig = px.line(m, x="period", y="sales", color=("branch" if branch == "All" else None), markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("monthly_sales_clean.csv missing or incomplete.")