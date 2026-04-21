"""
Maintenance Schedule page.
"""

from __future__ import annotations

import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.api_client import get_maintenance_schedule, get_schedule_summary
except ImportError:
    get_maintenance_schedule = None
    get_schedule_summary = None


def normalize_schedule_dataframe(raw_schedule):
    """Normalize schedule records into a page-ready DataFrame."""
    if raw_schedule is None:
        return pd.DataFrame()

    if isinstance(raw_schedule, pd.DataFrame):
        df = raw_schedule.copy()
    else:
        df = pd.DataFrame(raw_schedule)

    if df.empty:
        return df

    if "equipment" not in df.columns and "equipment_id" in df.columns:
        df["equipment"] = df["equipment_id"]
    if "type" not in df.columns:
        df["type"] = "Predictive"
    if "priority" not in df.columns and "priority_tier" in df.columns:
        df["priority"] = df["priority_tier"].str.title()
    if "priority" not in df.columns:
        df["priority"] = "Medium"
    if "job_id" not in df.columns:
        df["job_id"] = df.get("id", pd.Series(range(1, len(df) + 1))).apply(lambda value: f"JOB-{value}")
    if "assigned_to" not in df.columns:
        df["assigned_to"] = df.get("assigned_team", "Team A")
    if "estimated_cost" not in df.columns:
        df["estimated_cost"] = 0.0
    if "status" not in df.columns:
        df["status"] = "scheduled"

    if "start_time" not in df.columns and "scheduled_window_start" in df.columns:
        df["start_time"] = df["scheduled_window_start"]
    if "end_time" not in df.columns and "scheduled_window_end" in df.columns:
        df["end_time"] = df["scheduled_window_end"]

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["duration_days"] = ((df["end_time"] - df["start_time"]).dt.total_seconds() / 86400).clip(lower=0.1)
    df["status"] = df["status"].astype(str).str.replace("_", " ").str.title()

    return df


def show():
    """Render Maintenance Schedule page."""
    st.header("Maintenance Schedule")
    st.divider()

    raw_schedule = get_maintenance_schedule(days=7) if get_maintenance_schedule else []
    df_schedule = normalize_schedule_dataframe(raw_schedule)

    st.sidebar.header("Schedule Filters")
    job_type_filter = st.sidebar.multiselect("Job Type", options=sorted(df_schedule["type"].unique()) if not df_schedule.empty else [])
    priority_filter = st.sidebar.multiselect("Priority", options=sorted(df_schedule["priority"].unique()) if not df_schedule.empty else [])
    status_filter = st.sidebar.multiselect("Status", options=sorted(df_schedule["status"].unique()) if not df_schedule.empty else [])

    filtered_df = df_schedule.copy()
    if job_type_filter:
        filtered_df = filtered_df[filtered_df["type"].isin(job_type_filter)]
    if priority_filter:
        filtered_df = filtered_df[filtered_df["priority"].isin(priority_filter)]
    if status_filter:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]

    summary = get_schedule_summary(days=7) if get_schedule_summary else None
    total_jobs = int(summary["total_jobs"]) if summary else len(filtered_df)
    total_cost = float(summary["total_cost"]) if summary else filtered_df["estimated_cost"].sum() if not filtered_df.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", total_jobs)
    with col2:
        st.metric("Scheduled", int(summary["scheduled"]) if summary else len(filtered_df[filtered_df["status"] == "Scheduled"]))
    with col3:
        st.metric("In Progress", int(summary["in_progress"]) if summary else len(filtered_df[filtered_df["status"] == "In Progress"]))
    with col4:
        st.metric("Total Est. Cost", f"Rs {total_cost:,.0f}")

    st.divider()
    st.subheader("7 Day Schedule")

    if filtered_df.empty:
        st.info("No maintenance jobs match the selected filters.")
    else:
        priority_colors = {
            "Critical": "#D32F2F",
            "Warning": "#F57C00",
            "High": "#F57C00",
            "Medium": "#FBC02D",
            "Low": "#7CB342",
            "Normal": "#7CB342",
        }
        fig = go.Figure()
        for _, row in filtered_df.sort_values(["priority", "start_time"]).iterrows():
            fig.add_trace(
                go.Bar(
                    y=[f"{row['equipment']} - {row['job_id']}"],
                    x=[row["duration_days"]],
                    base=row["start_time"],
                    orientation="h",
                    marker_color=priority_colors.get(row["priority"], "#2196F3"),
                    customdata=[[row["status"], row["assigned_to"], row.get("recommended_action", "")]],
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Start: %{base|%Y-%m-%d %H:%M}<br>"
                        "Duration: %{x:.1f} days<br>"
                        "Status: %{customdata[0]}<br>"
                        "Assigned: %{customdata[1]}<br>"
                        "Action: %{customdata[2]}<extra></extra>"
                    ),
                    showlegend=False,
                )
            )
        fig.update_layout(height=480, xaxis_type="date", xaxis_title="Date", yaxis_title="Equipment / Job")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Job Prioritization")
        priority_order = {"Critical": 0, "Warning": 1, "High": 1, "Medium": 2, "Low": 3, "Normal": 3}
        display_df = filtered_df.copy()
        display_df["priority_sort"] = display_df["priority"].map(priority_order).fillna(99)
        display_df = display_df.sort_values(["priority_sort", "start_time"]).drop(columns=["priority_sort"])
        st.dataframe(
            display_df[
                [
                    "job_id",
                    "equipment",
                    "priority",
                    "status",
                    "assigned_to",
                    "estimated_duration_hours",
                    "estimated_cost",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Export Schedule")
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"maintenance_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        disabled=filtered_df.empty,
    )

    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__" or st.session_state.get("_running_in_streamlit", False):
    show()
