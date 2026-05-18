import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NKL Advanced Analytics Dashboard",
    page_icon="🏉",
    layout="wide"
)

# ─────────────────────────────────────────────
# WATERMARK
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 10px;
        right: 20px;
        opacity: 0.4;
        font-size: 12px;
    }
    </style>
    <div class="watermark">Made by Alson Adhikari</div>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("players_clean.csv")

    # numeric safety conversion
    num_cols = df.columns.drop(["team", "player", "role", "url", "profile"], errors="ignore")
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ──────────────── CORE METRICS ────────────────

    df["efficiency"] = df["total_points"] / df["matches"].replace(0, 1)

    df["raid_efficiency"] = df["successful_raids"] / (
        df["successful_raids"] + df["unsuccessful_raids"]
    ).replace(0, 1)

    df["defensive_index"] = (
        df["successful_tackles"] * 2 +
        df["super_tackles"] * 3 +
        df["tackle_points"]
    ) / df["matches"].replace(0, 1)

    df["clutch_index"] = df["do_or_die_points"] / df["total_points"].replace(0, 1)

    # ──────────────── ROLE FIX (CRITICAL FIX) ────────────────
    df["role_clean"] = np.where(
        df["tackle_points"] > df["raid_points"] * 1.2,
        "Defender",
        np.where(
            df["raid_points"] > df["tackle_points"] * 1.2,
            "Raider",
            "All Rounder"
        )
    )

    return df


df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.title("🏉 NKL Filters")

teams = ["All"] + sorted(df["team"].unique().tolist())
roles = ["All"] + sorted(df["role_clean"].unique().tolist())

sel_team = st.sidebar.selectbox("Team", teams)
sel_role = st.sidebar.selectbox("Role", roles)

min_pts = st.sidebar.slider(
    "Min Total Points",
    0, int(df["total_points"].max()), 0
)

min_matches = st.sidebar.slider(
    "Min Matches",
    0, int(df["matches"].max()), 0
)

# ─────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────
fdf = df.copy()

if sel_team != "All":
    fdf = fdf[fdf["team"] == sel_team]

if sel_role != "All":
    fdf = fdf[fdf["role_clean"] == sel_role]

fdf = fdf[
    (fdf["total_points"] >= min_pts) &
    (fdf["matches"] >= min_matches)
]

# ─────────────────────────────────────────────
# TEAM METRICS FIX (IMPORTANT)
# ─────────────────────────────────────────────
team_summary = df.groupby("team").agg({
    "matches": "max",
    "total_points": "sum",
    "raid_points": "sum",
    "tackle_points": "sum",
    "super_raids": "sum",
    "super_tackles": "sum"
}).reset_index()

team_summary["points_per_match"] = (
    team_summary["total_points"] /
    team_summary["matches"].replace(0, 1)
)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🏅 Nepal Kabaddi League Analytics Dashboard")
st.caption(f"Showing {len(fdf)} players out of {len(df)}")

st.divider()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", len(fdf))
c2.metric("Total Points", int(fdf["total_points"].sum()))
c3.metric("Avg Efficiency", round(fdf["efficiency"].mean(), 2))
c4.metric("Teams", fdf["team"].nunique())

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Attack",
    "Defense",
    "All Rounders"
])

# ─────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────
with tab1:
    st.subheader("Team Performance")

    fig = px.bar(
        team_summary,
        x="team",
        y="points_per_match",
        color="points_per_match"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Players")
    top_players = fdf.nlargest(10, "total_points")

    fig2 = px.bar(
        top_players,
        x="total_points",
        y="player",
        orientation="h",
        color="team"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# TAB 2 — ATTACK ANALYSIS
# ─────────────────────────────────────────────
with tab2:
    st.subheader("Raid Performance")

    fig = px.scatter(
        fdf,
        x="raid_points",
        y="successful_raids",
        size="total_points",
        color="role_clean",
        hover_name="player"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Raiders")
    top_raiders = fdf.nlargest(10, "raid_points")

    fig2 = px.bar(
        top_raiders,
        x="raid_points",
        y="player",
        orientation="h",
        color="team"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# TAB 3 — DEFENSE (FIXED)
# ─────────────────────────────────────────────
with tab3:
    st.subheader("Defensive Index Leaders")

    top_def = fdf.nlargest(10, "defensive_index")

    fig = px.bar(
        top_def,
        x="defensive_index",
        y="player",
        orientation="h",
        color="team"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tackle Contribution")

    fig2 = px.scatter(
        fdf,
        x="tackle_points",
        y="super_tackles",
        color="role_clean",
        size="defensive_index",
        hover_name="player"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# TAB 4 — ALL ROUNDERS (FIXED)
# ─────────────────────────────────────────────
with tab4:
    ar = fdf[fdf["role_clean"] == "All Rounder"]

    if ar.empty:
        st.warning("No All-Rounders in current filter")
    else:
        st.subheader("All Rounder Analysis")

        fig = px.scatter(
            ar,
            x="raid_points",
            y="tackle_points",
            size="total_points",
            color="team",
            hover_name="player"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Balanced Contribution")

        ar_table = ar[[
            "player",
            "team",
            "total_points",
            "raid_points",
            "tackle_points",
            "efficiency",
            "defensive_index"
        ]].sort_values("total_points", ascending=False)

        st.dataframe(ar_table, use_container_width=True)

# ─────────────────────────────────────────────
# DOWNLOAD
# ─────────────────────────────────────────────
csv = fdf.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Data",
    csv,
    "nkl_data.csv",
    "text/csv"
)
