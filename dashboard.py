import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NKL Analytics Dashboard",
    page_icon="🏉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════
# CUSTOM CSS
# ════════════════════════════════════════════════════════════

custom_css = """
<style>

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main Layout */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 95%;
}

/* Metric Cards */
div[data-testid="metric-container"] {
    background: linear-gradient(
        145deg,
        #1f2937,
        #111827
    );
    border: 1px solid #374151;
    padding: 16px;
    border-radius: 16px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
}

.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 10px 18px;
}

/* Watermark */
.watermark {
    position: fixed;
    bottom: 14px;
    right: 18px;
    background: rgba(20,20,20,0.45);
    backdrop-filter: blur(6px);
    padding: 8px 14px;
    border-radius: 12px;
    font-size: 13px;
    color: white;
    z-index: 999999;
    pointer-events: none;
    opacity: 0.7;
}

</style>
"""

st.markdown(
    custom_css,
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# WATERMARK
# ════════════════════════════════════════════════════════════

st.markdown(
    """
    <div class="watermark">
        NKL Analytics • Built by Alson Adhikari
    </div>
    """,
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════
# LOAD DATA
# ════════════════════════════════════════════════════════════

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

    # Advanced Metrics

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

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════

try:
    st.sidebar.image(
        "assets/nkl_logo.png",
        width=180
    )
except:
    st.sidebar.title("🏉 NKL")

st.sidebar.title("Dashboard Filters")

teams = ["All"] + sorted(
    df["team"].dropna().unique()
)

roles = ["All"] + sorted(
    df["role"].dropna().unique()
)

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
    "Minimum Matches Played",
    0,
    int(df["matches"].max()),
    0
)

# ════════════════════════════════════════════════════════════
# FILTER DATA
# ════════════════════════════════════════════════════════════

fdf = df.copy()

if selected_team != "All":
    fdf = fdf[
        fdf["team"] == selected_team
    ]

if selected_role != "All":
    fdf = fdf[
        fdf["role"] == selected_role
    ]

if search_player:
    fdf = fdf[
        fdf["player"].str.contains(
            search_player,
            case=False,
            na=False
        )
    ]

fdf = fdf[
    fdf["total_points"] >= min_points
]

fdf = fdf[
    fdf["matches"] >= min_matches
]

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

st.title("🏆 Nepal Kabaddi League Analytics Dashboard")

st.caption(
    f"Showing {len(fdf)} filtered players from NKL Season 1"
)

st.divider()

# ════════════════════════════════════════════════════════════
# KPI CARDS
# ════════════════════════════════════════════════════════════

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
    int(
        fdf.groupby("team")["matches"]
        .max()
        .sum()
    )
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
    "Do-or-Die Pts",
    int(fdf["do_or_die_points"].sum())
)

st.divider()

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Raid Analysis",
    "Defense",
    "Player Analytics"
])

# ════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════

with tab1:

    st.subheader("📊 League Overview")

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("### 🏅 Top 10 Scorers")

        top10 = fdf.nlargest(
            10,
            "total_points"
        )

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
            height=420,
            margin=dict(l=0,r=0,t=20,b=0),
            xaxis_title="Points",
            yaxis_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:

        st.markdown("### 📈 Team Ranking")

        team_rank = (
            fdf.groupby("team")
            .agg({
                "total_points":"sum",
                "matches":"max"
            })
            .reset_index()
        )

        team_rank["points_per_match"] = (
            team_rank["total_points"] /
            team_rank["matches"].replace(0,1)
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
            height=420,
            margin=dict(l=0,r=0,t=20,b=0),
            xaxis_title="Points Per Match",
            yaxis_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ════════════════════════════════════════════════════════════
# TAB 2 — RAID ANALYSIS
# ════════════════════════════════════════════════════════════

with tab2:

    st.subheader("⚔️ Raid Analysis")

    r1, r2 = st.columns(2)

    with r1:

        st.markdown("### Successful vs Unsuccessful Raids")

        raid_df = (
            fdf.groupby("team")[
                [
                    "successful_raids",
                    "unsuccessful_raids"
                ]
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

    st.markdown("### 🚨 Clutch Raiders")

    clutch = fdf.nlargest(
        10,
        "clutch_index"
    )

    fig = px.scatter(
        clutch,
        x="raid_points",
        y="do_or_die_points",
        size="super_raids",
        color="team",
        hover_name="player",
        size_max=40
    )

    fig.update_layout(
        height=420
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ════════════════════════════════════════════════════════════
# TAB 3 — DEFENSE ANALYSIS
# ════════════════════════════════════════════════════════════

with tab3:

    st.subheader("🛡️ Defense Analysis")

    d1, d2 = st.columns(2)

    with d1:

        st.markdown("### Team Defense")

        defense = (
            fdf.groupby("team")[
                [
                    "successful_tackles",
                    "super_tackles"
                ]
            ]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            defense,
            x="team",
            y=[
                "successful_tackles",
                "super_tackles"
            ],
            barmode="group",
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

    with d2:

        st.markdown("### Top Tacklers")

        top_tacklers = fdf.nlargest(
            10,
            "successful_tackles"
        )

        fig = px.bar(
            top_tacklers,
            x="successful_tackles",
            y="player",
            orientation="h",
            color="team",
            text="successful_tackles"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=380
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ════════════════════════════════════════════════════════════
# TAB 4 — PLAYER ANALYTICS
# ════════════════════════════════════════════════════════════

with tab4:

    st.subheader("⚡ Player Analytics")

    # PLAYER COMPARISON

    players = sorted(
        fdf["player"]
        .dropna()
        .unique()
    )

    if len(players) >= 2:

        pcol1, pcol2 = st.columns(2)

        player1_name = pcol1.selectbox(
            "Select Player 1",
            players,
            index=0
        )

        player2_name = pcol2.selectbox(
            "Select Player 2",
            players,
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
            fdf["player"] == player1_name
        ].iloc[0]

        p2 = fdf[
            fdf["player"] == player2_name
        ].iloc[0]

        rc1, rc2 = st.columns(2)

        with rc1:

            radar1 = go.Figure()

            radar1.add_trace(
                go.Scatterpolar(
                    r=[p1[m] for m in metrics],
                    theta=metrics,
                    fill='toself',
                    name=player1_name
                )
            )

            radar1.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True)
                ),
                showlegend=False,
                title=player1_name,
                height=450
            )

            st.plotly_chart(
                radar1,
                use_container_width=True
            )

        with rc2:

            radar2 = go.Figure()

            radar2.add_trace(
                go.Scatterpolar(
                    r=[p2[m] for m in metrics],
                    theta=metrics,
                    fill='toself',
                    name=player2_name
                )
            )

            radar2.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True)
                ),
                showlegend=False,
                title=player2_name,
                height=450
            )

            st.plotly_chart(
                radar2,
                use_container_width=True
            )

        compare_df = pd.DataFrame({
            "Metric": metrics,
            player1_name: [
                p1[m] for m in metrics
            ],
            player2_name: [
                p2[m] for m in metrics
            ]
        })

        st.dataframe(
            compare_df,
            use_container_width=True
        )

    else:

        st.warning(
            "Not enough players available."
        )

    st.divider()

    st.markdown("### 📋 Full Player Database")

    st.dataframe(
        fdf.drop(
            columns=["url"],
            errors="ignore"
        )
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
        "⬇ Download Filtered CSV",
        csv,
        "nkl_filtered.csv",
        "text/csv"
    )
