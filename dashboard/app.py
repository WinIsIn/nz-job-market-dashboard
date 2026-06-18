"""
NZ Tech Job Market Dashboard — Streamlit front-end.

All data comes from the local SQLite database populated by the pipeline or seed script.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd

from src.queries import (
    ensure_db,
    get_jobs_by_role_type,
    get_top_skills,
    get_jobs_by_city,
    get_salary_by_role,
    get_hiring_companies,
    get_jobs_over_time,
    get_last_updated,
    get_summary_stats,
)

DB_PATH = "data/jobs.db"

# Seed demo data on first run (database absent on Streamlit Cloud cold starts)
ensure_db(DB_PATH)

# ── Brand palette (teal family) ───────────────────────────────────────────────
PALETTE = ["#1D9E75", "#0F6E56", "#9FE1CB", "#5DCAA5", "#085041"]

# ── Cached query wrappers ─────────────────────────────────────────────────────
# TTL of 1 hour so a long-running dashboard picks up fresh pipeline runs.


@st.cache_data(ttl=3600)
def cached_role_counts(roles: tuple, cities: tuple) -> pd.DataFrame:
    df = get_jobs_by_role_type(DB_PATH)
    if roles:
        df = df[df["role_type"].isin(roles)]
    return df


@st.cache_data(ttl=3600)
def cached_top_skills(roles: tuple, cities: tuple) -> pd.DataFrame:
    return get_top_skills(15, DB_PATH)


@st.cache_data(ttl=3600)
def cached_city_counts(roles: tuple, cities: tuple) -> pd.DataFrame:
    df = get_jobs_by_city(DB_PATH)
    if cities:
        df = df[df["city"].isin(cities)]
    return df


@st.cache_data(ttl=3600)
def cached_salary_by_role(roles: tuple, cities: tuple) -> pd.DataFrame:
    df = get_salary_by_role(DB_PATH)
    if roles:
        df = df[df["role_type"].isin(roles)]
    return df


@st.cache_data(ttl=3600)
def cached_companies() -> pd.DataFrame:
    return get_hiring_companies(10, DB_PATH)


@st.cache_data(ttl=3600)
def cached_jobs_over_time() -> pd.DataFrame:
    df = get_jobs_over_time(DB_PATH)
    return df.iloc[::-1].reset_index(drop=True)  # oldest → newest for the line chart


@st.cache_data(ttl=3600)
def cached_stats() -> dict:
    return get_summary_stats(DB_PATH)


@st.cache_data(ttl=3600)
def cached_last_updated() -> str:
    return get_last_updated(DB_PATH)


@st.cache_data(ttl=3600)
def cached_all_roles() -> list[str]:
    df = get_jobs_by_role_type(DB_PATH)
    return sorted(df["role_type"].tolist())


@st.cache_data(ttl=3600)
def cached_all_cities() -> list[str]:
    df = get_jobs_by_city(DB_PATH)
    return sorted(df["city"].tolist())


# ── Page header ───────────────────────────────────────────────────────────────

st.title("NZ Tech Job Market Dashboard")
st.markdown("*Insights from NZ job listings — updated weekly*")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filters")
    st.caption(f"Data last updated: **{cached_last_updated()}**")
    st.markdown("---")

    all_roles = cached_all_roles()
    selected_roles = st.multiselect("Role type", options=all_roles, default=[])

    all_cities = cached_all_cities()
    selected_cities = st.multiselect("City", options=all_cities, default=[])

    st.markdown("---")
    st.caption("Data source: [Adzuna Jobs API](https://developer.adzuna.com/)")

# Convert to tuples so they can be used as @st.cache_data hash keys
role_filter = tuple(selected_roles)
city_filter = tuple(selected_cities)

# ── Row 1: KPI metric cards ───────────────────────────────────────────────────

stats = cached_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs Tracked", f"{stats['total_jobs']:,}")
col2.metric(
    "Avg Salary (NZD)",
    f"${stats['avg_salary']:,.0f}" if stats["avg_salary"] else "N/A",
)
col3.metric("Top City", stats["top_city"])
col4.metric("Most In-Demand Skill", stats["top_skill"])

st.markdown("###")

# ── Row 2: Skills bar chart + City donut ─────────────────────────────────────

col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("Top 15 In-Demand Skills")
    skills_df = cached_top_skills(role_filter, city_filter)
    if not skills_df.empty:
        fig = px.bar(
            skills_df.sort_values("count"),
            x="count",
            y="skill",
            orientation="h",
            labels={"count": "Mentions", "skill": ""},
            color="skill",
            color_discrete_sequence=PALETTE,
        )
        fig.update_layout(showlegend=False, margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skill data available.")

with col_right:
    st.subheader("Jobs by City")
    city_df = cached_city_counts(role_filter, city_filter)
    if not city_df.empty:
        fig = px.pie(
            city_df,
            names="city",
            values="job_count",
            hole=0.45,
            color_discrete_sequence=PALETTE,
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No city data available.")

# ── Row 3: Role breakdown + Salary by role ────────────────────────────────────

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Jobs by Role Type")
    role_df = cached_role_counts(role_filter, city_filter)
    if not role_df.empty:
        fig = px.bar(
            role_df,
            x="role_type",
            y="job_count",
            labels={"role_type": "Role", "job_count": "Jobs"},
            color="role_type",
            color_discrete_sequence=PALETTE,
        )
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No role data available.")

with col_right2:
    st.subheader("Avg Salary by Role Type (NZD)")
    salary_df = cached_salary_by_role(role_filter, city_filter)
    if not salary_df.empty:
        # Melt to long form for a grouped bar chart
        melted = salary_df.melt(
            id_vars="role_type",
            value_vars=["avg_salary_min", "avg_salary_max"],
            var_name="salary_type",
            value_name="salary",
        )
        melted["salary_type"] = melted["salary_type"].map(
            {"avg_salary_min": "Min", "avg_salary_max": "Max"}
        )
        fig = px.bar(
            melted,
            x="role_type",
            y="salary",
            color="salary_type",
            barmode="group",
            labels={"role_type": "Role", "salary": "NZD / year", "salary_type": ""},
            color_discrete_sequence=[PALETTE[0], PALETTE[2]],
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        fig.update_yaxes(tickprefix="$", tickformat=",")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No salary data available.")

# ── Row 4: Jobs posted per week ───────────────────────────────────────────────

st.markdown("###")
st.subheader("Jobs Posted Per Week (Last 8 Weeks)")
time_df = cached_jobs_over_time()
if not time_df.empty:
    fig = px.line(
        time_df,
        x="week",
        y="job_count",
        labels={"week": "Week", "job_count": "Jobs Posted"},
        markers=True,
        color_discrete_sequence=[PALETTE[0]],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    fig.update_traces(line_width=2.5)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No timeline data available.")

# ── Row 5: Top hiring companies ───────────────────────────────────────────────

st.markdown("###")
st.subheader("Top 10 Hiring Companies")
companies_df = cached_companies()
if not companies_df.empty:
    companies_df.index = range(1, len(companies_df) + 1)
    companies_df.columns = ["Company", "Open Listings"]
    st.dataframe(companies_df, use_container_width=True)
else:
    st.info("No company data available.")
