
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="NKL Dashboard",
    page_icon="🏉",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    div[data-testid="metric-container"] {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load Data ───────────────────────────────────────────────────────────────
@st.cache_data
def load():
    df = pd.read_csv("players_clean.csv")
    num_cols = [
        "total_points","matches","raid_points","tackle_points",
        "successful_raids","super_raids","successful_tackles",
        "super_tackles","do_or_die_points","unsuccessful_raids",
        "super_5s","avg_raid_pts_match",
        "raid_success_rate","raid_contribution","tackle_contribution"
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
            # Raid Efficiency %
df["raid_efficiency"] = (
    df["successful_raids"] /
    (
        df["successful_raids"] +
        df["unsuccessful_raids"]
    ).replace(0, 1)
) * 100

# Tackle Efficiency
df["tackle_efficiency"] = (
    df["successful_tackles"] /
    df["matches"].replace(0, 1)
)

# Clutch Index
df["clutch_index"] = (
    df["do_or_die_points"] /
    df["total_points"].replace(0, 1)
) * 100
return df

df = load()

# ── Sidebar Filters ─────────────────────────────────────────────────────────
st.sidebar.image("https://nepalkabaddileague.com/logo.png", width=160, use_column_width=False)
st.sidebar.title("🏉 NKL Filters")

teams    = ["All"] + sorted(df["team"].unique().tolist())
roles    = ["All"] + sorted(df["role"].unique().tolist())
sel_team = st.sidebar.selectbox("Team",  teams)
sel_role = st.sidebar.selectbox("Role",  roles)
search_player = st.sidebar.text_input("🔍 Search Player")
min_pts  = st.sidebar.slider(
    "Min Total Points", 0, int(df["total_points"].max()), 0
)
min_matches = st.sidebar.slider(
    "Min Matches Played", 0, int(df["matches"].max()), 0
)

fdf = df.copy()
if sel_team != "All":
    fdf = fdf[fdf["team"] == sel_team]
if sel_role != "All":
    fdf = fdf[fdf["role"] == sel_role]
    if search_player:
    fdf = fdf[
        fdf["player"]
        .str.contains(search_player, case=False, na=False)
    ]
fdf = fdf[fdf["total_points"] >= min_pts]
fdf = fdf[fdf["matches"] >= min_matches]

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — HEADER + LEAGUE KPIs
# ══════════════════════════════════════════════════════════════════════════════
st.title("🏅 Nepal Kabaddi League — Season 1 Dashboard")
st.caption(f"Showing **{len(fdf)}** of **{len(df)}** players")
st.divider()

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Players",            len(fdf))
c2.metric("Total Points",       int(fdf["total_points"].sum()))
c3.metric("Team Matches",  int(fdf.groupby("team")["matches"].max().sum())) 
c4.metric("Super Raids",        int(fdf["super_raids"].sum()))
c5.metric("Super Tackles",      int(fdf["super_tackles"].sum()))
c6.metric("Super 5s",           int(fdf["super_5s"].sum()))

st.divider()
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Raid Analysis",
    "Defense",
    "Player Analytics"
])

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — TOP SCORERS + TEAM POINTS
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📊 Scoring Overview")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🏆 Top 10 Scorers**")
    top10 = fdf.nlargest(10, "total_points")
    fig = px.bar(
        top10, x="total_points", y="player",
        orientation="h", color="team", text="total_points",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        showlegend=True,
        margin=dict(l=0,r=0,t=10,b=0),
        height=380,
        xaxis_title="Points",
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:

    st.markdown("**🏆 Team Performance Ranking**")

    team_rank = (
        fdf.groupby("team")
        .agg({
            "total_points":"sum",
            "successful_raids":"sum",
            "successful_tackles":"sum",
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
        margin=dict(l=0,r=0,t=10,b=0),
        height=380,
        xaxis_title="Points Per Match",
        yaxis_title=""
    )

    st.plotly_chart(fig, use_container_width=True)
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0,r=0,t=10,b=0),
        height=380
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — RAID ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("⚔️ Raid Analysis")
col3, col4 = st.columns(2)

with col3:
    st.markdown("**Raid Efficiency by Team (Successful vs Unsuccessful)**")
    raid_df = fdf.groupby("team")[["successful_raids","unsuccessful_raids"]].sum().reset_index()
    raid_df["success_rate"] = (
        raid_df["successful_raids"] /
        (raid_df["successful_raids"] + raid_df["unsuccessful_raids"])
        .replace(0,1) * 100
    ).round(1)
    fig = px.bar(
        raid_df, x="team",
        y=["successful_raids","unsuccessful_raids"],
        barmode="stack",
        color_discrete_map={
            "successful_raids":   "#2ecc71",
            "unsuccessful_raids": "#e74c3c"
        },
        text_auto=True
    )
    fig.update_layout(
        margin=dict(l=0,r=0,t=10,b=0),
        height=340,
        xaxis_tickangle=-20,
        legend_title="",
        xaxis_title="", yaxis_title="Raids"
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.markdown("**Top 10 — Avg Raid Pts / Match**")
    raiders = fdf[fdf["matches"] > 0].nlargest(10, "avg_raid_pts_match")
    fig = px.bar(
        raiders, x="avg_raid_pts_match", y="player",
        orientation="h", color="team", text="avg_raid_pts_match",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        margin=dict(l=0,r=0,t=10,b=0),
        height=340,
        xaxis_title="Avg Pts/Match", yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

col5, col6 = st.columns(2)

with col5:
    st.markdown("**Super Raids by Team**")
    sr = fdf.groupby("team")[["super_raids","super_5s"]].sum().reset_index()
    fig = px.bar(
        sr, x="team", y=["super_raids","super_5s"],
        barmode="group",
        color_discrete_map={"super_raids":"#f39c12","super_5s":"#9b59b6"},
        text_auto=True
    )
    fig.update_layout(
        margin=dict(l=0,r=0,t=10,b=0), height=300,
        xaxis_tickangle=-20, legend_title="",
        xaxis_title="", yaxis_title="Count"
    )
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.markdown("**Do or Die Points — Top 10**")
    dod = fdf.nlargest(10, "do_or_die_points")
    fig = px.bar(
        dod, x="do_or_die_points", y="player",
        orientation="h", color="team", text="do_or_die_points",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"), showlegend=False,
        margin=dict(l=0,r=0,t=10,b=0), height=300,
        xaxis_title="Do or Die Pts", yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — TACKLE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("🛡️ Tackle Analysis")
col7, col8 = st.columns(2)

with col7:
    st.markdown("**Successful vs Super Tackles by Team**")
    tack = fdf.groupby("team")[["successful_tackles","super_tackles"]].sum().reset_index()
    fig = px.bar(
        tack, x="team", y=["successful_tackles","super_tackles"],
        barmode="group",
        color_discrete_map={
            "successful_tackles": "#3498db",
            "super_tackles":      "#1abc9c"
        },
        text_auto=True
    )
    fig.update_layout(
        margin=dict(l=0,r=0,t=10,b=0), height=320,
        xaxis_tickangle=-20, legend_title="",
        xaxis_title="", yaxis_title="Tackles"
    )
    st.plotly_chart(fig, use_container_width=True)

with col8:
    st.markdown("**Top 10 Tacklers**")
    top_tack = fdf.nlargest(10, "successful_tackles")
    fig = px.bar(
        top_tack, x="successful_tackles", y="player",
        orientation="h", color="team", text="successful_tackles",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"), showlegend=False,
        margin=dict(l=0,r=0,t=10,b=0), height=320,
        xaxis_title="Successful Tackles", yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — ALL-ROUNDER BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("🔄 All-Rounder Deep Dive")

ar = fdf[fdf["role"] == "All Rounder"].copy()

if ar.empty:
    st.info("No All-Rounders match current filters.")
else:
    a1,a2,a3,a4 = st.columns(4)
    a1.metric("All-Rounders",         len(ar))
    a2.metric("Total Raid Pts",        int(ar["raid_points"].sum()))
    a3.metric("Total Tackle Pts",      int(ar["tackle_points"].sum()))
    a4.metric("Avg Raid/Tackle Ratio",
              round(ar["raid_points"].sum() /
                    max(ar["tackle_points"].sum(), 1), 2))

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Raid vs Tackle Split per All-Rounder**")
        ar_s = ar.sort_values("total_points", ascending=False)
        fig = px.bar(
            ar_s, x="player", y=["raid_points","tackle_points"],
            barmode="stack",
            color_discrete_map={
                "raid_points":   "#e74c3c",
                "tackle_points": "#3498db"
            },
            hover_data=["team","total_points"]
        )
        fig.update_layout(
            xaxis_tickangle=-40,
            margin=dict(l=0,r=0,t=10,b=0), height=380,
            legend_title="", xaxis_title="", yaxis_title="Points"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Raid-type vs Tackle-type All-Rounders**")
        max_val = max(ar["raid_points"].max(), ar["tackle_points"].max()) + 5
        fig = px.scatter(
            ar, x="raid_points", y="tackle_points",
            size="total_points", color="team",
            hover_name="player", size_max=35,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.add_shape(
            type="line", x0=0, y0=0, x1=max_val, y1=max_val,
            line=dict(color="gray", dash="dot", width=1)
        )
        fig.add_annotation(
            x=max_val*0.65, y=max_val*0.75,
            text="Equal contribution",
            showarrow=False, font=dict(color="gray", size=11)
        )
        fig.update_layout(
            margin=dict(l=0,r=0,t=10,b=0), height=380,
            xaxis_title="Raid Points", yaxis_title="Tackle Points"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**All-Rounder Stats Table**")
    ar_table = ar.copy()
    ar_table["profile"] = ar_table.apply(
        lambda r: "🗡️ Raid-heavy"    if r["raid_contribution"] >= 60
             else "🛡️ Tackle-heavy"  if r["tackle_contribution"] >= 40
             else "⚖️ Balanced", axis=1
    )
    st.dataframe(
        ar_table[[
            "player","team","total_points","matches",
            "raid_points","tackle_points",
            "raid_contribution","tackle_contribution","profile",
            "super_raids","super_tackles","avg_raid_pts_match"
        ]].sort_values("total_points", ascending=False),
        use_container_width=True, height=320
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — ADVANCED PLAYER COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("⚡ Advanced Player Comparison")

all_names = sorted(fdf["player"].unique().tolist())

col_p1, col_p2 = st.columns(2)

p1 = col_p1.selectbox(
    "Select Player 1",
    all_names,
    index=0
)

p2 = col_p2.selectbox(
    "Select Player 2",
    all_names,
    index=min(1, len(all_names)-1)
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

player1 = fdf[fdf["player"] == p1].iloc[0]
player2 = fdf[fdf["player"] == p2].iloc[0]

# Radar Charts
c1, c2 = st.columns(2)

with c1:

    fig1 = go.Figure()

    fig1.add_trace(go.Scatterpolar(
        r=[player1[m] for m in metrics],
        theta=metrics,
        fill='toself',
        name=p1
    ))

    fig1.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        title=p1,
        height=450
    )

    st.plotly_chart(fig1, use_container_width=True)

with c2:

    fig2 = go.Figure()

    fig2.add_trace(go.Scatterpolar(
        r=[player2[m] for m in metrics],
        theta=metrics,
        fill='toself',
        name=p2
    ))

    fig2.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        title=p2,
        height=450
    )

    st.plotly_chart(fig2, use_container_width=True)

# Side-by-Side Stats Table
compare_df = pd.DataFrame({
    "Metric": metrics,
    p1: [player1[m] for m in metrics],
    p2: [player2[m] for m in metrics]
})

st.dataframe(compare_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — FULL PLAYER TABLE
# ══════════════════════════════════════════════════════════════════════════════
csv = fdf.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Filtered Data",
    csv,
    "nkl_filtered.csv",
    "text/csv"
)
st.subheader("📋 Full Player Stats Table")
st.dataframe(
    fdf.drop(columns=["url"], errors="ignore")
       .sort_values("total_points", ascending=False)
       .reset_index(drop=True),
    use_container_width=True,
    height=450
)
