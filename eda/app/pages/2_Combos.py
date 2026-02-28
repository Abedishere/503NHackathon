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

st.title("Product Combinations (Combos)")

kpis = load("branch_kpis.csv")
pairs_all = load("combo_pairs_scored_all_branches.csv")

if pairs_all.empty:
    st.warning("Missing combo_pairs_scored_all_branches.csv – run pipeline.")
    st.stop()

branches = ["All"] + sorted(pairs_all["branch"].dropna().unique().tolist())
branch = st.sidebar.selectbox("Branch", branches)

df = pairs_all if branch == "All" else pairs_all[pairs_all["branch"] == branch]
df["lift"] = pd.to_numeric(df["lift"], errors="coerce")
df["pair_customers"] = pd.to_numeric(df["pair_customers"], errors="coerce")
df["uplift_spend"] = pd.to_numeric(df.get("uplift_spend", None), errors="coerce")

st.subheader("Top pairs")
st.dataframe(df.head(50), use_container_width=True)

st.subheader("Lift vs Support (customers)")
plot_df = df.dropna(subset=["lift","pair_customers"]).head(200)
plot_df["pair"] = plot_df["item_a"].astype(str) + " + " + plot_df["item_b"].astype(str)
fig = px.scatter(plot_df, x="pair_customers", y="lift", hover_name="pair")
st.plotly_chart(fig, use_container_width=True)

if "uplift_spend" in df.columns and df["uplift_spend"].notna().any():
    st.subheader("Value uplift proxy (using customer total spend)")
    fig2 = px.bar(df.dropna(subset=["uplift_spend"]).head(25),
                  x="uplift_spend",
                  y=df["item_a"].astype(str) + " + " + df["item_b"].astype(str),
                  orientation="h")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Uplift requires customer totals (rep_s_00150). If missing, uplift is NaN.")