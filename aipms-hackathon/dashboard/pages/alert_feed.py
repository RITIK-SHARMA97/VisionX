"""
Alert Feed page.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.api_client import acknowledge_alert, get_alert_stats, get_alerts
except ImportError:
    acknowledge_alert = None
    get_alert_stats = None
    get_alerts = None


def normalize_alerts_dataframe(raw_alerts):
    """Normalize alert records into a page-ready DataFrame."""
    if raw_alerts is None:
        return pd.DataFrame()

    if isinstance(raw_alerts, pd.DataFrame):
        df = raw_alerts.copy()
    else:
        df = pd.DataFrame(raw_alerts)

    if df.empty:
        return df

    if "alert_id" not in df.columns:
        df["alert_id"] = df.get("id", pd.Series(range(1, len(df) + 1))).apply(lambda value: f"ALR-{value}")
    if "timestamp" not in df.columns:
        df["timestamp"] = df.get("triggered_at", datetime.now().isoformat())
    if "equipment" not in df.columns:
        df["equipment"] = df.get("equipment_id", "Unknown")
    if "type" not in df.columns:
        df["type"] = df.get("failure_mode_hint", "Condition Alert")
    if "description" not in df.columns:
        df["description"] = df.get("message", "No description available")
    if "value" not in df.columns:
        df["value"] = df.get("failure_prob", 0.0)
    if "threshold" not in df.columns:
        df["threshold"] = 0.70
    if "acknowledged_by" not in df.columns:
        df["acknowledged_by"] = None

    df["severity"] = df["severity"].astype(str).str.title()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["acknowledged"] = df["acknowledged"].fillna(False).astype(bool)

    return df


def show():
    """Render Alert Feed page."""
    st.header("Real-Time Alert Feed")
    st.divider()

    raw_alerts = get_alerts(days=7) if get_alerts else []
    df_alerts = normalize_alerts_dataframe(raw_alerts)
    stats = get_alert_stats() if get_alert_stats else None

    if df_alerts.empty:
        st.info("No alerts available right now.")
        return

    st.sidebar.header("Alert Filters")
    severity_filter = st.sidebar.multiselect(
        "Severity Level",
        options=sorted(df_alerts["severity"].unique()),
        default=["Critical", "Warning"] if {"Critical", "Warning"}.issubset(set(df_alerts["severity"])) else list(df_alerts["severity"].unique()),
    )
    ack_filter = st.sidebar.radio("Acknowledgement Status", options=["All", "Unacknowledged", "Acknowledged"], index=1)
    equipment_filter = st.sidebar.multiselect("Equipment", options=sorted(df_alerts["equipment"].unique()))

    filtered_alerts = df_alerts.copy()
    if severity_filter:
        filtered_alerts = filtered_alerts[filtered_alerts["severity"].isin(severity_filter)]
    if ack_filter == "Unacknowledged":
        filtered_alerts = filtered_alerts[~filtered_alerts["acknowledged"]]
    elif ack_filter == "Acknowledged":
        filtered_alerts = filtered_alerts[filtered_alerts["acknowledged"]]
    if equipment_filter:
        filtered_alerts = filtered_alerts[filtered_alerts["equipment"].isin(equipment_filter)]

    filtered_alerts = filtered_alerts.sort_values("timestamp", ascending=False)

    total_alerts = int(stats["total_alerts"]) if stats else len(df_alerts)
    unack_alerts = int(stats["unacknowledged"]) if stats else len(df_alerts[~df_alerts["acknowledged"]])
    crit_alerts = int(stats["critical"]) if stats else len(df_alerts[df_alerts["severity"] == "Critical"])
    high_alerts = int(stats["high"]) if stats else len(df_alerts[df_alerts["severity"].isin(["Critical", "Warning"])])
    ack_percent = float(stats["acknowledged_percent"]) if stats else ((len(df_alerts[df_alerts["acknowledged"]]) / len(df_alerts)) * 100)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Alerts", total_alerts)
    with col2:
        st.metric("Unacknowledged", unack_alerts)
    with col3:
        st.metric("Critical", crit_alerts)
    with col4:
        st.metric("High / Warning", high_alerts)
    with col5:
        st.metric("Acknowledged %", f"{ack_percent:.1f}%")

    st.divider()
    st.subheader("Alert Trend (Last 24 Hours)")
    now = datetime.now()
    hours = [now - timedelta(hours=hour) for hour in range(24, 0, -1)]
    hourly_counts = [
        len(df_alerts[(df_alerts["timestamp"] >= hour) & (df_alerts["timestamp"] < hour + timedelta(hours=1))])
        for hour in hours
    ]
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=[hour.strftime("%H:%M") for hour in hours],
            y=hourly_counts,
            mode="lines+markers",
            line=dict(color="#FF6B6B", width=2),
        )
    )
    fig_trend.update_layout(height=300, xaxis_title="Time", yaxis_title="Number of Alerts")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()
    st.subheader("Alert Feed")

    if filtered_alerts.empty:
        st.info("No alerts match the selected filters.")
    else:
        display_alerts = filtered_alerts.copy()
        display_alerts["timestamp_str"] = display_alerts["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        display_alerts["age_minutes"] = ((datetime.now() - display_alerts["timestamp"]).dt.total_seconds() / 60).round(0).astype(int)
        table_df = display_alerts[
            [
                "alert_id",
                "timestamp_str",
                "age_minutes",
                "severity",
                "type",
                "equipment",
                "description",
                "acknowledged",
                "acknowledged_by",
            ]
        ].copy()
        table_df.columns = ["Alert ID", "Timestamp", "Age (min)", "Severity", "Type", "Equipment", "Description", "Ack.", "Ack. By"]
        st.dataframe(table_df, use_container_width=True, hide_index=True)

        first_unack = filtered_alerts[~filtered_alerts["acknowledged"]]
        if not first_unack.empty and acknowledge_alert:
            alert_to_ack = first_unack.iloc[0]
            if st.button(f"Acknowledge {alert_to_ack['alert_id']}"):
                response = acknowledge_alert(int(str(alert_to_ack.get("id", 0)).replace("ALR-", "") or 0), "demo_user")
                if response:
                    st.success(f"Alert {alert_to_ack['alert_id']} acknowledged.")

    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# ═════════════════════════════════════════════════════════════════
# Module-level execution for direct page access
# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    show()
else:
    # When imported, also run show() so page is rendered
    try:
        show()
    except Exception:
        pass  # Page may already be shown by parent app
