"""
Plant manager KPI dashboard page.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.api_client import get_dashboard_kpi, get_fleet_overview, get_maintenance_schedule
except ImportError:
    get_dashboard_kpi = None
    get_fleet_overview = None
    get_maintenance_schedule = None


def show():
    """Render KPI dashboard page."""
    st.header("Plant Manager KPI Dashboard")
    kpi = get_dashboard_kpi() if get_dashboard_kpi else {}
    fleet = get_fleet_overview() if get_fleet_overview else []
    schedule = get_maintenance_schedule(days=7) if get_maintenance_schedule else []

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Equipment", kpi.get("total_equipment", len(fleet)))
    with col2:
        st.metric("Critical Assets", kpi.get("critical_count", 0))
    with col3:
        st.metric("Warnings", kpi.get("warning_count", 0))
    with col4:
        st.metric("7 Day Cost", f"Rs {kpi.get('estimated_cost_7day', 0):,.0f}")

    st.divider()

    if fleet:
        df_fleet = pd.DataFrame(fleet)
        fig = px.bar(
            df_fleet,
            x="id",
            y="failure_prob",
            color="status",
            title="Failure Probability by Equipment",
            color_discrete_map={"critical": "#dc3545", "warning": "#ffc107", "normal": "#28a745", "offline": "#6c757d"},
        )
        st.plotly_chart(fig, use_container_width=True)

    if schedule:
        df_schedule = pd.DataFrame(schedule)
        st.subheader("Upcoming Jobs")
        st.dataframe(
            df_schedule[["equipment_id", "priority_tier", "recommended_action", "estimated_duration_hours"]],
            use_container_width=True,
            hide_index=True,
        )

    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__" or st.session_state.get("_running_in_streamlit", False):
    show()
