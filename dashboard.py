import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NKL Analytics Dashboard",
    page_icon="🏉",
    layout="wide"
)

# ─────────────────────────────────────────────
# WATERMARK
# ─────────────────────────────────────────────
st.markdown("""
<style>
.footer {
    position: fixed;
    bottom: 10px;
    right: 20px;
    font-size: 12px;
    color: gray;
}
</style>
<div class="footer">Made by Alson Adhikari</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("players_clean.csv")

    # numeric cleanup
    num_cols = df.columns.drop(["team", "player", "role", "url", "profile"], errors="ignore")
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ───────── ROLE NORMALIZATION ENGINE ─────────
    def normalize_role(r):
        r = str(r).strip().lower()
        if r in ["defender", "defence", "defense"]:
            return "Defender"
        elif r in ["raider"]:
            return "Raider"
        elif r in ["all rounder", "allrounder"]:
            return "All Rounder"
        else:
            return "Unknown"

    df["role"] = df["role"].apply(normalize_role)

    # ───────── FIX UNKNOWN ROLE LOGIC ─────────
    df.loc[
        (df["role"] == "Unknown") & (df["tackle_points"] > df["raid_points"]),
        "role"
    ] = "Defender"

    df.loc[
        (df["role"] == "Unknown") & (df["raid_points"] > df["tackle_points"]),
        "role"
    ] = "Raider"

    # ───────── ADVANCED METRICS ─────────
    df["raid_efficiency"] = (
        df["successful_raids"] /
        (df["successful_raids"] + df["unsuccessful_raids"]).replace(0, 1)
    ) * 100

    df["clutch_index"] = (
        df["do_or_die_points"] /
        df["total_points"].replace(0, 1)
    ) * 100

    df["impact_score"] = (
        df["total_points"] +
        df["raid_points"] * 0.8 +
        df["tackle_points"] * 0.9 +
        df["super_raids"] * 2 +
        df["super_tackles"] * 2
    ) / df["matches"].replace(0, 1)

    return df


df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS (ONLY SAFE FILTERS)
# ─────────────────────────────────────────────
st.sidebar.title("🏉 NKL Filters")

teams = ["All"] + sorted(df["team"].unique().tolist())

sel_team = st.sidebar.selectbox("Team", teams)
search = st.sidebar.text_input("Search Player")
min_matches = st.sidebar.slider(
    "Min Matches", 0, int(df["matches"].max()), 0
)

# ─────────────────────────────────────────────
# DATA LAYERS (IMPORTANT FIX)
# ─────────────────────────────────────────────
df_master = df.copy()

df_team = df_master[df_master["team"] == sel_team] if sel_team != "All" else df_master.copy()

df_player = df_team.copy()

if search:
    df_player = df_player[df_player["player"].str.contains(search, case=False)]

df_player = df_player[df_player["matches"] >= min_matches]

# ─────────────────────────────────────────────
# LEAGUE KPIs (GLOBAL - NEVER FILTERED)
# ─────────────────────────────────────────────
st.title("🏅 Nepal Kabaddi League Analytics Dashboard")
st.caption(f"Showing {len(df_player)} players")

league_matches = df_master.groupby("team")["matches"].max().sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", len(df_player))
c2.metric("Total Points", int(df_master["total_points"].sum()))
c3.metric("League Matches", int(league_matches))
c4.metric("Teams", df_master["team"].nunique())

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Attack",
    "Defense",
    "Players"
])

# ─────────────────────────────────────────────
# OVERVIEW (GLOBAL + TEAM MIX)
# ─────────────────────────────────────────────
with tab1:
    st.subheader("League Overview")

    top_players = df_master.nlargest(10, "total_points")

    fig = px.bar(
        top_players,
        x="total_points",
        y="player",
        color="team",
        orientation="h"
    )
    st.plotly_chart(fig, use_container_width=True)

    team_stats = df_master.groupby("team")[["total_points","raid_points","tackle_points"]].sum().reset_index()

    fig2 = px.bar(
        team_stats,
        x="team",
        y=["raid_points","tackle_points"],
        barmode="group"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# ATTACK ANALYSIS
# ─────────────────────────────────────────────
with tab2:
    st.subheader("Raider Analysis")

    raiders = df_master[df_master["role"] == "Raider"]

    fig = px.bar(
        raiders.nlargest(10, "raid_points"),
        x="raid_points",
        y="player",
        orientation="h",
        color="team"
    )
    st.plotly_chart(fig, use_container_width=True)

    team_raid = raiders.groupby("team")[["raid_points","super_raids"]].sum().reset_index()

    fig2 = px.bar(
        team_raid,
        x="team",
        y="raid_points"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# DEFENSE ANALYSIS (FIXED)
# ─────────────────────────────────────────────
with tab3:
    st.subheader("Defender Analysis")

    defenders = df_master[df_master["role"] == "Defender"]

    if defenders.empty:
        st.warning("No defender data found after normalization")
    else:
        fig = px.bar(
            defenders.nlargest(10, "tackle_points"),
            x="tackle_points",
            y="player",
            orientation="h",
            color="team"
        )
        st.plotly_chart(fig, use_container_width=True)

        team_def = defenders.groupby("team")[["tackle_points","super_tackles"]].sum().reset_index()

        fig2 = px.bar(
            team_def,
            x="team",
            y="tackle_points"
        )
        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# PLAYER ANALYTICS (FILTERED)
# ─────────────────────────────────────────────
with tab4:
    st.subheader("Player Analytics")

    st.dataframe(
        df_player.sort_values("total_points", ascending=False),
        use_container_width=True
    )

    fig = px.scatter(
        df_player,
        x="raid_points",
        y="tackle_points",
        size="total_points",
        color="team",
        hover_name="player"
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# DOWNLOAD
# ─────────────────────────────────────────────
csv = df_player.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Data",
    csv,
    "nkl_data.csv",
    "text/csv"
)
