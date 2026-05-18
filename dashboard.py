import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NKL Analytics Pro",
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
    right: 15px;
    font-size: 12px;
    color: gray;
}
</style>
<div class="footer">Made by Alson Adhikari</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("players_clean.csv")

    # numeric safety
    for col in df.columns:
        if col not in ["team", "player", "role", "url", "profile"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ─────────────────────────────────────────────
    # ROLE NORMALIZATION ENGINE (CRITICAL FIX)
    # ─────────────────────────────────────────────
    def normalize_role(r):
        r = str(r).strip().lower()

        if r in ["defender", "defence", "defense"]:
            return "Defender"
        elif r == "raider":
            return "Raider"
        elif r in ["all rounder", "allrounder"]:
            return "All Rounder"
        else:
            return "Unknown"

    df["role"] = df["role"].apply(normalize_role)

    # ─────────────────────────────────────────────
    # SMART UNKNOWN RECLASSIFICATION
    # ─────────────────────────────────────────────
    df.loc[
        (df["role"] == "Unknown") & (df["tackle_points"] > df["raid_points"]),
        "role"
    ] = "Defender"

    df.loc[
        (df["role"] == "Unknown") & (df["raid_points"] > df["tackle_points"]),
        "role"
    ] = "Raider"

    df.loc[
        (df["role"] == "Unknown"),
        "role"
    ] = "All Rounder"

    # ─────────────────────────────────────────────
    # ADVANCED METRICS
    # ─────────────────────────────────────────────
    df["raid_efficiency"] = (
        df["successful_raids"] /
        (df["successful_raids"] + df["unsuccessful_raids"]).replace(0, 1)
    ) * 100

    df["impact_score"] = (
        df["total_points"] +
        df["raid_points"] * 0.8 +
        df["tackle_points"] * 1.1 +
        df["super_raids"] * 2 +
        df["super_tackles"] * 2
    ) / df["matches"].replace(0, 1)

    return df


df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR (ONLY SAFE FILTERS)
# ─────────────────────────────────────────────
st.sidebar.title("🏉 NKL Filters")

teams = ["All"] + sorted(df["team"].unique().tolist())

selected_team = st.sidebar.selectbox("Team", teams)
search_player = st.sidebar.text_input("Search Player")
min_matches = st.sidebar.slider("Min Matches", 0, int(df["matches"].max()), 0)

# ─────────────────────────────────────────────
# DATA LAYERS (CRITICAL ARCHITECTURE FIX)
# ─────────────────────────────────────────────

# MASTER DATA (NEVER FILTERED)
df_master = df.copy()

# TEAM DATA (ONLY TEAM FILTER)
if selected_team == "All":
    df_team = df_master.copy()
else:
    df_team = df_master[df_master["team"] == selected_team]

# PLAYER DATA (ONLY HERE FILTERS APPLY)
df_player = df_team.copy()

if search_player:
    df_player = df_player[
        df_player["player"].str.contains(search_player, case=False, na=False)
    ]

df_player = df_player[df_player["matches"] >= min_matches]

# ─────────────────────────────────────────────
# FIXED MATCH LOGIC (IMPORTANT)
# ─────────────────────────────────────────────
league_matches = df_master.groupby("team")["matches"].max().sum()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🏅 Nepal Kabaddi League Analytics Dashboard")
st.caption(f"Showing {len(df_player)} players")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", len(df_player))
c2.metric("Total Points", int(df_master["total_points"].sum()))
c3.metric("League Matches", int(league_matches))
c4.metric("Teams", df_master["team"].nunique())

st.divider()

# ─────────────────────────────────────────────
# ROLE SPLITS (FIXED SYSTEM)
# ─────────────────────────────────────────────
raiders = df_master[df_master["role"] == "Raider"]
defenders = df_master[df_master["role"] == "Defender"]
all_rounders = df_master[df_master["role"] == "All Rounder"]

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
# OVERVIEW (GLOBAL)
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

    team_stats = df_master.groupby("team")[["total_points", "raid_points", "tackle_points"]].sum().reset_index()

    fig2 = px.bar(
        team_stats,
        x="team",
        y=["raid_points", "tackle_points"],
        barmode="group"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# ATTACK ANALYSIS
# ─────────────────────────────────────────────
with tab2:
    st.subheader("Raid Analysis")

    if raiders.empty:
        st.warning("No Raider data available")
    else:
        fig = px.bar(
            raiders.nlargest(10, "raid_points"),
            x="raid_points",
            y="player",
            orientation="h",
            color="team"
        )
        st.plotly_chart(fig, use_container_width=True)

    team_raid = raiders.groupby("team")[["raid_points", "super_raids"]].sum().reset_index()

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
    st.subheader("Defense Analysis")

    if defenders.empty:
        st.warning("No Defender data found")
    else:
        fig = px.bar(
            defenders.nlargest(10, "tackle_points"),
            x="tackle_points",
            y="player",
            orientation="h",
            color="team"
        )
        st.plotly_chart(fig, use_container_width=True)

    team_def = defenders.groupby("team")[["tackle_points", "super_tackles"]].sum().reset_index()

    fig2 = px.bar(
        team_def,
        x="team",
        y="tackle_points"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# ALL ROUNDER ANALYSIS (FIXED SECTION)
# ─────────────────────────────────────────────
with tab4:
    st.subheader("All Rounder Analysis")

    if all_rounders.empty:
        st.info("No All Rounder data available")
    else:
        fig = px.bar(
            all_rounders.nlargest(10, "total_points"),
            x="total_points",
            y="player",
            orientation="h",
            color="team"
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.scatter(
            all_rounders,
            x="raid_points",
            y="tackle_points",
            size="total_points",
            color="team",
            hover_name="player"
        )
        st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# PLAYER TABLE (FILTERED VIEW)
# ─────────────────────────────────────────────
st.divider()
st.subheader("Player Database")

st.dataframe(
    df_player.sort_values("total_points", ascending=False),
    use_container_width=True
)

# ─────────────────────────────────────────────
# DOWNLOAD BUTTON
# ─────────────────────────────────────────────
csv = df_player.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Data",
    csv,
    "nkl_dashboard_data.csv",
    "text/csv"
)
