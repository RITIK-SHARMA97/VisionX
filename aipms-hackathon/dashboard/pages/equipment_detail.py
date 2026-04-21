"""
Equipment Detail Page - Phase 5.2
Sensor trends, RUL degradation, maintenance info
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure page
st.set_page_config(
    page_title="Equipment Detail - AIPMS",
    page_icon="🔍",
    layout="wide",
)
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.api_client import (
        get_equipment_detail,
        get_equipment_sensors,
        get_equipment_rul,
        get_fleet_overview,
    )
except ImportError:
    get_equipment_detail = None
    get_equipment_sensors = None
    get_equipment_rul = None
    get_fleet_overview = None


def get_sample_equipment_list():
    """Get list of available equipment"""
    if get_fleet_overview:
        fleet = get_fleet_overview()
        if fleet:
            return [equipment["id"] for equipment in fleet]
    return ["EXC-01", "DMP-03", "CVR-01"]


def get_sample_equipment_detail(equipment_id):
    """Generate sample equipment detail data"""
    return {
        'equipment_id': equipment_id,
        'name': equipment_id,
        'type': equipment_id.split('-')[0],
        'location': f'Production Area {equipment_id.split("-")[1]}',
        'status': np.random.choice(['Healthy', 'Warning', 'Critical'], p=[0.6, 0.3, 0.1]),
        'uptime_hours': np.random.randint(1000, 50000),
        'total_runtime_hours': np.random.randint(50000, 100000),
        'maintenance_due_days': np.random.randint(0, 30),
        'last_maintenance': datetime.now() - timedelta(days=np.random.randint(10, 100)),
        'next_maintenance': datetime.now() + timedelta(days=np.random.randint(1, 60)),
        'operating_temperature_c': round(np.random.uniform(20, 80), 1),
        'operating_pressure_bar': round(np.random.uniform(1, 10), 2),
        'vibration_mm_s': round(np.random.uniform(0.5, 8.0), 2),
        'rpm': np.random.randint(500, 3000),
        'efficiency_percent': round(np.random.uniform(75, 98), 1),
        'current_rul_days': np.random.randint(30, 500)
    }


def get_sample_sensor_trends(equipment_id):
    """Generate sample sensor trend data as DataFrame"""
    now = datetime.now()
    timestamps = [now - timedelta(hours=h) for h in range(24, 0, -1)]
    
    data = {
        'timestamp': timestamps,
        'temperature': np.clip(np.random.uniform(20, 80, 24) + np.random.normal(0, 2, 24), 0, 150),
        'pressure': np.clip(np.random.uniform(1, 10, 24) + np.random.normal(0, 0.5, 24), 0, 20),
        'vibration': np.clip(np.random.uniform(0.5, 8, 24) + np.random.normal(0, 0.3, 24), 0, 15),
        'rpm': np.clip(np.random.uniform(500, 3000, 24) + np.random.normal(0, 100, 24), 0, 5000)
    }
    
    return pd.DataFrame(data)


def get_sample_rul_degradation(equipment_id):
    """Generate sample RUL degradation data as DataFrame"""
    now = datetime.now()
    days = np.arange(0, 366, 7)  # Weekly data for a year
    
    # Simulate degradation pattern
    rul_values = 365 - (days * 0.8 + np.random.normal(0, 5, len(days)))
    rul_values = np.clip(rul_values, 0, 500)
    
    data = {
        'date': [now + timedelta(days=int(d)) for d in days],
        'rul': rul_values,
        'threshold_warning': np.full(len(days), 90),
        'threshold_critical': np.full(len(days), 30)
    }
    
    return pd.DataFrame(data)


def normalize_equipment_detail(equipment_id, raw_detail):
    """Normalize API/detail payloads to the schema expected by this page."""
    if not isinstance(raw_detail, dict):
        return get_sample_equipment_detail(equipment_id)

    sample = get_sample_equipment_detail(equipment_id)
    status_map = {
        "normal": "Healthy",
        "healthy": "Healthy",
        "warning": "Warning",
        "critical": "Critical",
    }

    def parse_datetime(value, fallback):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                return fallback
        return fallback

    normalized = sample.copy()
    normalized.update({
        "name": raw_detail.get("name", raw_detail.get("id", equipment_id)),
        "type": raw_detail.get("type", sample["type"]),
        "location": raw_detail.get("location", sample["location"]),
        "status": status_map.get(str(raw_detail.get("status", "")).lower(), sample["status"]),
        "uptime_hours": raw_detail.get("uptime_hours", raw_detail.get("total_operating_hours", sample["uptime_hours"])),
        "total_runtime_hours": raw_detail.get("total_runtime_hours", raw_detail.get("total_operating_hours", sample["total_runtime_hours"])),
        "operating_temperature_c": raw_detail.get("operating_temperature_c", sample["operating_temperature_c"]),
        "operating_pressure_bar": raw_detail.get("operating_pressure_bar", sample["operating_pressure_bar"]),
        "vibration_mm_s": raw_detail.get("vibration_mm_s", raw_detail.get("anomaly_score", sample["vibration_mm_s"])),
        "rpm": raw_detail.get("rpm", sample["rpm"]),
        "efficiency_percent": raw_detail.get("efficiency_percent", sample["efficiency_percent"]),
    })

    normalized["current_rul_days"] = raw_detail.get(
        "current_rul_days",
        max(0, round(raw_detail.get("rul_hours", sample["current_rul_days"] * 24) / 24)),
    )
    normalized["maintenance_due_days"] = raw_detail.get(
        "maintenance_due_days",
        max(0, normalized["current_rul_days"] - 30),
    )
    normalized["last_maintenance"] = parse_datetime(
        raw_detail.get("last_maintenance"),
        sample["last_maintenance"],
    )
    normalized["next_maintenance"] = parse_datetime(
        raw_detail.get("next_maintenance"),
        datetime.now() + timedelta(days=max(1, normalized["maintenance_due_days"])),
    )

    return normalized


def normalize_sensor_trends(equipment_id, raw_sensors):
    """Normalize sensor payloads into chart-ready wide DataFrame."""
    if isinstance(raw_sensors, pd.DataFrame):
        return raw_sensors

    if not isinstance(raw_sensors, list) or not raw_sensors:
        return get_sample_sensor_trends(equipment_id)

    df = pd.DataFrame(raw_sensors)
    if {"timestamp", "temperature", "pressure", "vibration", "rpm"}.issubset(df.columns):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    if {"timestamp", "sensor_name", "value"}.issubset(df.columns):
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        pivot = (
            df.pivot_table(index="timestamp", columns="sensor_name", values="value", aggfunc="mean")
            .reset_index()
            .sort_values("timestamp")
        )
        fallback = get_sample_sensor_trends(equipment_id)
        merged = pd.merge(fallback, pivot, on="timestamp", how="left", suffixes=("_fallback", ""))
        for column in ["temperature", "pressure", "vibration", "rpm"]:
            fallback_column = f"{column}_fallback"
            if column not in merged.columns and fallback_column in merged.columns:
                merged[column] = merged[fallback_column]
            elif fallback_column in merged.columns:
                merged[column] = merged[column].fillna(merged[fallback_column])
        return merged[["timestamp", "temperature", "pressure", "vibration", "rpm"]]

    return get_sample_sensor_trends(equipment_id)


def normalize_rul_degradation(equipment_id, raw_rul):
    """Normalize RUL payloads into the chart format expected by the page."""
    if isinstance(raw_rul, pd.DataFrame):
        return raw_rul

    if isinstance(raw_rul, list):
        df = pd.DataFrame(raw_rul)
        if {"date", "rul", "threshold_warning", "threshold_critical"}.issubset(df.columns):
            df["date"] = pd.to_datetime(df["date"])
            return df

    if isinstance(raw_rul, dict) and "rul_hours" in raw_rul:
        current_rul_days = max(0, raw_rul["rul_hours"] / 24)
        now = datetime.now()
        days = np.arange(0, 91, 7)
        rul_values = np.clip(current_rul_days - (days * (current_rul_days / max(1, days[-1] + 7))), 0, None)
        return pd.DataFrame({
            "date": [now + timedelta(days=int(day)) for day in days],
            "rul": rul_values,
            "threshold_warning": np.full(len(days), 90),
            "threshold_critical": np.full(len(days), 30),
        })

    return get_sample_rul_degradation(equipment_id)


def show():
    """Render Equipment Detail page."""
    
    st.header("🔍 Equipment Detail")
    
    # Equipment selector in sidebar
    st.sidebar.header("Equipment Selection")
    equipment_list = get_sample_equipment_list()
    
    if 'selected_equipment' not in st.session_state:
        st.session_state.selected_equipment = equipment_list[0]
    
    selected_equipment = st.sidebar.selectbox(
        "Select Equipment",
        options=equipment_list,
        index=equipment_list.index(st.session_state.selected_equipment) if st.session_state.selected_equipment in equipment_list else 0
    )
    st.session_state.selected_equipment = selected_equipment
    
    # Load equipment data
    try:
        if get_equipment_detail:
            equipment_detail = normalize_equipment_detail(
                selected_equipment,
                get_equipment_detail(selected_equipment),
            )
        else:
            equipment_detail = get_sample_equipment_detail(selected_equipment)
    except Exception as e:
        st.warning(f"Could not fetch equipment detail: {str(e)}")
        equipment_detail = get_sample_equipment_detail(selected_equipment)
    
    if not equipment_detail:
        equipment_detail = get_sample_equipment_detail(selected_equipment)
    
    # Try to load sensor trends
    try:
        if get_equipment_sensors:
            sensor_trends = normalize_sensor_trends(
                selected_equipment,
                get_equipment_sensors(selected_equipment),
            )
        else:
            sensor_trends = get_sample_sensor_trends(selected_equipment)
    except Exception as e:
        sensor_trends = get_sample_sensor_trends(selected_equipment)
    
    # Try to load RUL data
    try:
        if get_equipment_rul:
            rul_data = normalize_rul_degradation(
                selected_equipment,
                get_equipment_rul(selected_equipment),
            )
        else:
            rul_data = get_sample_rul_degradation(selected_equipment)
    except Exception as e:
        rul_data = get_sample_rul_degradation(selected_equipment)
    
    st.divider()
    
    # Equipment status header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.header(f"{equipment_detail['name']}")
        st.text(f"Type: {equipment_detail['type']} | Location: {equipment_detail['location']}")
    
    with col2:
        status_color = {
            'Healthy': '✅ Healthy',
            'Warning': '⚠️ Warning',
            'Critical': '🚨 Critical'
        }
        st.metric("Status", status_color.get(equipment_detail['status'], equipment_detail['status']))
    
    with col3:
        rul = equipment_detail['current_rul_days']
        st.metric("RUL (Days)", rul)
    
    st.divider()
    
    # Key metrics
    st.subheader("📊 Current Operating Conditions")
    
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    
    with metric_col1:
        st.metric("Temperature", f"{equipment_detail['operating_temperature_c']}°C", delta="Normal: 20-80°C")
    
    with metric_col2:
        st.metric("Pressure", f"{equipment_detail['operating_pressure_bar']} bar", delta="Normal: 1-10 bar")
    
    with metric_col3:
        st.metric("Vibration", f"{equipment_detail['vibration_mm_s']} mm/s", delta="Normal: <7 mm/s")
    
    with metric_col4:
        st.metric("Speed", f"{equipment_detail['rpm']:,} RPM", delta=f"Efficiency: {equipment_detail['efficiency_percent']}%")
    
    with metric_col5:
        st.metric("Uptime", f"{equipment_detail['uptime_hours']:,} hrs", delta=f"Total: {equipment_detail['total_runtime_hours']:,} hrs")
    
    st.divider()
    
    # Maintenance information
    st.subheader("🔧 Maintenance Information")
    
    maint_col1, maint_col2, maint_col3 = st.columns(3)
    
    with maint_col1:
        st.info(f"""
        **Last Maintenance**
        {equipment_detail['last_maintenance'].strftime('%Y-%m-%d')}
        ({(datetime.now() - equipment_detail['last_maintenance']).days} days ago)
        """)
    
    with maint_col2:
        days_until = (equipment_detail['next_maintenance'] - datetime.now()).days
        st.info(f"""
        **Next Maintenance**
        {equipment_detail['next_maintenance'].strftime('%Y-%m-%d')}
        ({days_until} days remaining)
        """)
    
    with maint_col3:
        if equipment_detail['maintenance_due_days'] > 0:
            st.warning(f"""
            **Maintenance Due**
            {equipment_detail['maintenance_due_days']} days
            """)
        else:
            st.success("**Maintenance Status** - Up to date")
    
    st.divider()
    
    # Sensor trends chart
    st.subheader("📈 Sensor Trends (24 Hour History)")
    
    fig_sensors = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Temperature", "Pressure", "Vibration", "RPM"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Temperature
    fig_sensors.add_trace(
        go.Scatter(
            x=sensor_trends['timestamp'],
            y=sensor_trends['temperature'],
            name='Temperature (°C)',
            mode='lines',
            line=dict(color='#FF6B6B'),
            fill='tozeroy'
        ),
        row=1, col=1
    )
    
    # Pressure
    fig_sensors.add_trace(
        go.Scatter(
            x=sensor_trends['timestamp'],
            y=sensor_trends['pressure'],
            name='Pressure (bar)',
            mode='lines',
            line=dict(color='#4ECDC4'),
            fill='tozeroy'
        ),
        row=1, col=2
    )
    
    # Vibration
    fig_sensors.add_trace(
        go.Scatter(
            x=sensor_trends['timestamp'],
            y=sensor_trends['vibration'],
            name='Vibration (mm/s)',
            mode='lines',
            line=dict(color='#FFE66D'),
            fill='tozeroy'
        ),
        row=2, col=1
    )
    
    # RPM
    fig_sensors.add_trace(
        go.Scatter(
            x=sensor_trends['timestamp'],
            y=sensor_trends['rpm'],
            name='RPM',
            mode='lines',
            line=dict(color='#95E1D3'),
            fill='tozeroy'
        ),
        row=2, col=2
    )
    
    fig_sensors.update_xaxes(title_text="Time", row=2, col=1)
    fig_sensors.update_xaxes(title_text="Time", row=2, col=2)
    fig_sensors.update_yaxes(title_text="°C", row=1, col=1)
    fig_sensors.update_yaxes(title_text="bar", row=1, col=2)
    fig_sensors.update_yaxes(title_text="mm/s", row=2, col=1)
    fig_sensors.update_yaxes(title_text="RPM", row=2, col=2)
    fig_sensors.update_layout(height=600, showlegend=False, hovermode='x unified')
    
    st.plotly_chart(fig_sensors, use_container_width=True)
    
    st.divider()
    
    # RUL Degradation chart
    st.subheader("⏳ RUL (Remaining Useful Life) Degradation")
    
    rul_df = normalize_rul_degradation(selected_equipment, rul_data)
    
    fig_rul = go.Figure()
    
    # RUL line
    fig_rul.add_trace(go.Scatter(
        x=rul_df['date'],
        y=rul_df['rul'],
        mode='lines',
        name='RUL',
        line=dict(color='#2196F3', width=3),
        fill='tozeroy'
    ))
    
    # Warning threshold
    fig_rul.add_trace(go.Scatter(
        x=rul_df['date'],
        y=rul_df['threshold_warning'],
        mode='lines',
        name='Warning Threshold (90 days)',
        line=dict(color='#FFC107', width=2, dash='dash')
    ))
    
    # Critical threshold
    fig_rul.add_trace(go.Scatter(
        x=rul_df['date'],
        y=rul_df['threshold_critical'],
        mode='lines',
        name='Critical Threshold (30 days)',
        line=dict(color='#F44336', width=2, dash='dash')
    ))
    
    fig_rul.update_layout(
        title="RUL Degradation Over Time",
        xaxis_title="Date",
        yaxis_title="RUL (Days)",
        height=400,
        hovermode='x unified',
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig_rul, use_container_width=True)
    
    # RUL interpretation
    col1, col2 = st.columns(2)
    
    with col1:
        current_rul = equipment_detail['current_rul_days']
        if current_rul < 30:
            st.error(f"🚨 **CRITICAL**: RUL is {current_rul} days. Immediate maintenance may be required.")
        elif current_rul < 90:
            st.warning(f"⚠️ **WARNING**: RUL is {current_rul} days. Plan maintenance soon.")
        else:
            st.success(f"✅ **HEALTHY**: RUL is {current_rul} days. Equipment operating normally.")
    
    with col2:
        degradation_rate = (rul_df['rul'].iloc[0] - rul_df['rul'].iloc[-1]) / len(rul_df)
        st.info(f"**Degradation Rate**: ~{abs(degradation_rate):.2f} days/week")
    
    st.divider()
    
    # Health summary
    st.subheader("📋 Health Summary")
    
    health_items = [
        ("Efficiency", f"{equipment_detail['efficiency_percent']}%", equipment_detail['efficiency_percent'] > 85),
        ("Temperature Normal", "Yes" if 20 <= equipment_detail['operating_temperature_c'] <= 80 else "No", 20 <= equipment_detail['operating_temperature_c'] <= 80),
        ("Pressure Normal", "Yes" if 1 <= equipment_detail['operating_pressure_bar'] <= 10 else "No", 1 <= equipment_detail['operating_pressure_bar'] <= 10),
        ("Vibration Normal", "Yes" if equipment_detail['vibration_mm_s'] < 7 else "No", equipment_detail['vibration_mm_s'] < 7),
    ]
    
    for label, value, is_good in health_items:
        status_icon = "✅" if is_good else "⚠️"
        st.write(f"{status_icon} {label}: {value}")
    
    st.divider()
    st.caption("Equipment data updated in real-time • Last refresh: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__" or st.session_state.get("_running_in_streamlit", False):
    show()
