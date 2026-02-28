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

st.title("Staffing / Attendance")

staff = load("attendance_daily_hours.csv")
if staff.empty:
    st.warning("Missing attendance_daily_hours.csv – run pipeline.")
    st.stop()

staff["date_in_dt"] = pd.to_datetime(staff["date_in_dt"], errors="coerce")

branches = ["All"] + sorted(staff["branch"].dropna().unique().tolist())
branch = st.sidebar.selectbox("Branch", branches)

df = staff if branch == "All" else staff[staff["branch"] == branch]
st.dataframe(df.tail(30), use_container_width=True)

fig = px.line(df.sort_values("date_in_dt"), x="date_in_dt", y="total_hours",
              color=("branch" if branch == "All" else None), markers=True)
st.plotly_chart(fig, use_container_width=True)