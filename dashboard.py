import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ═════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NKL Analytics Dashboard",
    page_icon="🏉",
    layout="wide"
)

# ═════════════════════════════════════════════════════════════
# HIDE STREAMLIT BRANDING
# ═════════════════════════════════════════════════════════════

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

div[data-testid="metric-container"] {
    background-color: #1e1e2f;
    border: 1px solid #333;
    padding: 15px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
}

.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
}
</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
# LOAD DATA
# ═════════════════════════════════════════════════════════════

@st.cache_data
def load_data():

    df = pd.read_csv("players_clean.csv")

    numeric_cols = [
        "total_points",
        "matches",
        "raid_points",
        "tackle_points",
        "successful_raids",
        "super_raids",
        "successful_tackles",
        "super_tackles",
        "do_or_die_points",
        "unsuccessful_raids",
        "super_5s",
        "avg_raid_pts_match",
        "raid_success_rate",
        "raid_contribution",
        "tackle_contribution"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    # ADVANCED METRICS

    df["raid_efficiency"] = (
        df["successful_raids"] /
        (
            df["successful_raids"] +
            df["unsuccessful_raids"]
        ).replace(0, 1)
    ) * 100

    df["tackle_efficiency"] = (
        df["successful_tackles"] /
        df["matches"].replace(0, 1)
    )

    df["clutch_index"] = (
        df["do_or_die_points"] /
        df["total_points"].replace(0, 1)
    ) * 100

    return df


df = load_data()

# ═════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════

try:
    st.sidebar.image("assets/nkl_logo.png", width=180)
except:
    st.sidebar.title("🏉 NKL")

st.sidebar.title("Filters")

teams = ["All"] + sorted(df["team"].dropna().unique())
roles = ["All"] + sorted(df["role"].dropna().unique())

selected_team = st.sidebar.selectbox(
    "Select Team",
    teams
)

selected_role = st.sidebar.selectbox(
    "Select Role",
    roles
)

search_player = st.sidebar.text_input(
    "Search Player"
)

min_points = st.sidebar.slider(
    "Minimum Total Points",
    0,
    int(df["total_points"].max()),
    0
)

min_matches = st.sidebar.slider(
    "Minimum Matches",
    0,
    int(df["matches"].max()),
    0
)

# ═════════════════════════════════════════════════════════════
# FILTER DATA
# ═════════════════════════════════════════════════════════════

fdf = df.copy()

if selected_team != "All":
    fdf = fdf[fdf["team"] == selected_team]

if selected_role != "All":
    fdf = fdf[fdf["role"] == selected_role]

if search_player:
    fdf = fdf[
        fdf["player"].str.contains(
            search_player,
            case=False,
            na=False
        )
    ]

fdf = fdf[fdf["total_points"] >= min_points]
fdf = fdf[fdf["matches"] >= min_matches]

# ═════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════

st.title("🏆 Nepal Kabaddi League Analytics Dashboard")

st.caption(
    f"Showing {len(fdf)} players out of {len(df)} total players"
)

st.divider()

# ═════════════════════════════════════════════════════════════
# KPI SECTION
# ═════════════════════════════════════════════════════════════

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric(
    "Players",
    len(fdf)
)

k2.metric(
    "Total Points",
    int(fdf["total_points"].sum())
)

k3.metric(
    "Matches",
    int(fdf.groupby("team")["matches"].max().sum())
)

k4.metric(
    "Super Raids",
    int(fdf["super_raids"].sum())
)

k5.metric(
    "Super Tackles",
    int(fdf["super_tackles"].sum())
)

k6.metric(
    "Super 5s",
    int(fdf["super_5s"].sum())
)

st.divider()

# ═════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Raid Analysis",
    "Defense",
    "Player Analytics"
])

# ═════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═════════════════════════════════════════════════════════════

with tab1:

    st.subheader("📊 League Overview")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🏅 Top 10 Scorers")

        top10 = fdf.nlargest(10, "total_points")

        fig = px.bar(
            top10,
            x="total_points",
            y="player",
            orientation="h",
            color="team",
            text="total_points",
            color_discrete_sequence=px.colors.qualitative.Bold
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Points",
            yaxis_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        st.markdown("### 📈 Team Performance")

        team_rank = (
            fdf.groupby("team")
            .agg({
                "total_points": "sum",
                "matches": "max"
            })
            .reset_index()
        )

        team_rank["points_per_match"] = (
            team_rank["total_points"] /
            team_rank["matches"].replace(0, 1)
        ).round(2)

        fig = px.bar(
            team_rank.sort_values(
                "points_per_match",
                ascending=True
            ),
            x="points_per_match",
            y="team",
            orientation="h",
            color="points_per_match",
            text="points_per_match"
        )

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Points Per Match",
            yaxis_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ═════════════════════════════════════════════════════════════
# TAB 2 — RAID ANALYSIS
# ═════════════════════════════════════════════════════════════

with tab2:

    st.subheader("⚔️ Raid Analysis")

    r1, r2 = st.columns(2)

    with r1:

        st.markdown("### Raid Efficiency")

        raid_df = (
            fdf.groupby("team")[
                ["successful_raids", "unsuccessful_raids"]
            ]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            raid_df,
            x="team",
            y=[
                "successful_raids",
                "unsuccessful_raids"
            ],
            barmode="stack",
            text_auto=True
        )

        fig.update_layout(
            height=380,
            xaxis_tickangle=-20
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with r2:

        st.markdown("### Top Raiders")

        raiders = fdf.nlargest(
            10,
            "avg_raid_pts_match"
        )

        fig = px.bar(
            raiders,
            x="avg_raid_pts_match",
            y="player",
            orientation="h",
            color="team",
            text="avg_raid_pts_match"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=380
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    r3, r4 = st.columns(2)

    with r3:

        st.markdown("### Super Raids")

        sr = (
            fdf.groupby("team")[
                ["super_raids", "super_5s"]
            ]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            sr,
            x="team",
            y=["super_raids", "super_5s"],
            barmode="group",
            text_auto=True
        )

        fig.update_layout(height=320)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with r4:

        st.markdown("### Do or Die Specialists")

        dod = fdf.nlargest(
            10,
            "do_or_die_points"
        )

        fig = px.bar(
            dod,
            x="do_or_die_points",
            y="player",
            orientation="h",
            color="team",
            text="do_or_die_points"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=320
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ═════════════════════════════════════════════════════════════
# TAB 3 — DEFENSE
# ═════════════════════════════════════════════════════════════

with tab3:

    st.subheader("🛡️ Defense Analysis")

    d1, d2 = st.columns(2)

    with d1:

        st.markdown("### Team Tackle Performance")

        tack = (
            fdf.groupby("team")[
                ["successful_tackles", "super_tackles"]
            ]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            tack,
            x="team",
            y=[
                "successful_tackles",
                "super_tackles"
            ],
            barmode="group",
            text_auto=True
        )

        fig.update_layout(
            height=350,
            xaxis_tickangle=-20
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with d2:

        st.markdown("### Top Tacklers")

        top_tack = fdf.nlargest(
            10,
            "successful_tackles"
        )

        fig = px.bar(
            top_tack,
            x="successful_tackles",
            y="player",
            orientation="h",
            color="team",
            text="successful_tackles"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ═════════════════════════════════════════════════════════════
# TAB 4 — PLAYER ANALYTICS
# ═════════════════════════════════════════════════════════════

with tab4:

    st.subheader("⚡ Advanced Player Analytics")

    # ALL ROUNDERS

    ar = fdf[fdf["role"] == "All Rounder"]

    if not ar.empty:

        st.markdown("### 🔄 All-Rounder Analysis")

        fig = px.scatter(
            ar,
            x="raid_points",
            y="tackle_points",
            size="total_points",
            color="team",
            hover_name="player",
            size_max=35
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # PLAYER COMPARISON

    st.markdown("### 🆚 Player Comparison")

    all_names = sorted(
        fdf["player"].dropna().unique()
    )

    if len(all_names) >= 2:

        pc1, pc2 = st.columns(2)

        player_1 = pc1.selectbox(
            "Player 1",
            all_names,
            index=0
        )

        player_2 = pc2.selectbox(
            "Player 2",
            all_names,
            index=1
        )

        metrics = [
            "raid_points",
            "tackle_points",
            "successful_raids",
            "successful_tackles",
            "super_raids",
            "super_tackles",
            "do_or_die_points"
        ]

        p1 = fdf[
            fdf["player"] == player_1
        ].iloc[0]

        p2 = fdf[
            fdf["player"] == player_2
        ].iloc[0]

        c1, c2 = st.columns(2)

        with c1:

            radar1 = go.Figure()

            radar1.add_trace(
                go.Scatterpolar(
                    r=[p1[m] for m in metrics],
                    theta=metrics,
                    fill='toself',
                    name=player_1
                )
            )

            radar1.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True)
                ),
                showlegend=False,
                title=player_1,
                height=450
            )

            st.plotly_chart(
                radar1,
                use_container_width=True
            )

        with c2:

            radar2 = go.Figure()

            radar2.add_trace(
                go.Scatterpolar(
                    r=[p2[m] for m in metrics],
                    theta=metrics,
                    fill='toself',
                    name=player_2
                )
            )

            radar2.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True)
                ),
                showlegend=False,
                title=player_2,
                height=450
            )

            st.plotly_chart(
                radar2,
                use_container_width=True
            )

        compare_df = pd.DataFrame({
            "Metric": metrics,
            player_1: [p1[m] for m in metrics],
            player_2: [p2[m] for m in metrics]
        })

        st.dataframe(
            compare_df,
            use_container_width=True
        )

    else:
        st.warning(
            "Not enough players available for comparison."
        )

    st.divider()

    # PLAYER TABLE

    st.markdown("### 📋 Full Player Statistics")

    st.dataframe(
        fdf.drop(columns=["url"], errors="ignore")
        .sort_values(
            "total_points",
            ascending=False
        )
        .reset_index(drop=True),
        use_container_width=True,
        height=500
    )

    csv = fdf.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download Filtered Data",
        csv,
        "nkl_filtered.csv",
        "text/csv"
    )
