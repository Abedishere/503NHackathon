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

st.title("Coffee & Milkshake Growth Strategy")

growth = load("growth_metrics_all_branches.csv")
coffee_x = load("coffee_cross_sell_all_branches.csv")
milk_x = load("milkshake_cross_sell_all_branches.csv")

if growth.empty:
    st.warning("Missing growth_metrics_all_branches.csv – run pipeline.")
    st.stop()

branches = ["All"] + sorted(growth["branch"].dropna().unique().tolist())
branch = st.sidebar.selectbox("Branch", branches)

g = growth if branch == "All" else growth[growth["branch"] == branch]

st.subheader("Penetration + uplift")
st.dataframe(g, use_container_width=True)

fig = px.bar(g, x="segment", y="penetration_customers", color=("branch" if branch == "All" else None))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Cross-sell: Coffee buyers")
cx = coffee_x if branch == "All" else coffee_x[coffee_x["branch"] == branch]
if cx.empty:
    st.info("No coffee cross-sell table available for this selection.")
else:
    st.dataframe(cx.head(30), use_container_width=True)

st.subheader("Cross-sell: Milkshake buyers")
mx = milk_x if branch == "All" else milk_x[milk_x["branch"] == branch]
if mx.empty:
    st.info("No milkshake cross-sell table available for this selection.")
else:
    st.dataframe(mx.head(30), use_container_width=True)