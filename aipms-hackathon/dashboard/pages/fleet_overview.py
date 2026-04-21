"""
Fleet Overview Page
Equipment status grid, risk heatmap, KPI summary
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.api_client import (
    get_fleet_overview,
    status_badge,
    equipment_icon,
    format_timestamp,
)
from dashboard.config import COLORS


# Configure page
st.set_page_config(
    page_title="Fleet Overview - AIPMS",
    page_icon="⚙️",
    layout="wide",
)

def show():
    """Render Fleet Overview page."""
    
    st.header("📊 Fleet Overview")
    
    # Load data
    equipment_list = get_fleet_overview()
    
    if not equipment_list:
        st.warning("⚠️ No equipment data available. Start the FastAPI backend on http://localhost:8000")
        return
    
    # ════════════════════════════════════════════════════════════════
    # KPI METRICS
    # ════════════════════════════════════════════════════════════════
    
    critical_count = sum(1 for e in equipment_list if e.get("status") == "critical")
    warning_count = sum(1 for e in equipment_list if e.get("status") == "warning")
    normal_count = sum(1 for e in equipment_list if e.get("status") == "normal")
    offline_count = sum(1 for e in equipment_list if e.get("status") == "offline")
    
    total_failure_prob = sum(float(e.get("failure_prob", 0)) for e in equipment_list) / len(equipment_list) if equipment_list else 0
    avg_rul = sum(float(e.get("rul_hours", 0)) for e in equipment_list) / len(equipment_list) if equipment_list else 0
    
    st.subheader("Fleet Health Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        pct = (critical_count/len(equipment_list)*100) if equipment_list else 0
        st.metric(label="🔴 Critical", value=critical_count, delta=f"{pct:.1f}%")
    with col2:
        pct = (warning_count/len(equipment_list)*100) if equipment_list else 0
        st.metric(label="🟡 Warning", value=warning_count, delta=f"{pct:.1f}%")
    with col3:
        pct = (normal_count/len(equipment_list)*100) if equipment_list else 0
        st.metric(label="🟢 Normal", value=normal_count, delta=f"{pct:.1f}%")
    with col4:
        st.metric(label="⚫ Offline", value=offline_count)
    with col5:
        st.metric(label="📊 Total Fleet", value=len(equipment_list))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Avg Failure Prob", f"{total_failure_prob*100:.1f}%")
    with col2:
        st.metric("Avg RUL (hours)", f"{avg_rul:.1f}")
    
    st.divider()
    
    # ════════════════════════════════════════════════════════════════
    # PLOTLY VISUALIZATIONS
    # ════════════════════════════════════════════════════════════════
    
    col1, col2 = st.columns(2)
    
    # Status Distribution
    with col1:
        st.subheader("Status Distribution")
        status_dist = pd.DataFrame({
            'Status': ['Critical', 'Warning', 'Normal', 'Offline'],
            'Count': [critical_count, warning_count, normal_count, offline_count]
        })
        fig_dist = px.pie(status_dist, values='Count', names='Status', hole=0.3)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # Failure Probability Distribution
    with col2:
        st.subheader("Failure Probability Distribution")
        failure_probs = [float(e.get('failure_prob', 0)) for e in equipment_list]
        fig_fail = go.Figure(data=[
            go.Histogram(x=failure_probs, nbinsx=10, marker_color=COLORS.get('critical', '#dc3545'))
        ])
        fig_fail.update_layout(
            title="Distribution of Failure Probabilities",
            xaxis_title="Failure Probability",
            yaxis_title="Equipment Count",
            height=400,
        )
        st.plotly_chart(fig_fail, use_container_width=True)
    
    st.divider()
    
    # ════════════════════════════════════════════════════════════════
    # EQUIPMENT TABLE
    # ════════════════════════════════════════════════════════════════
    
    st.subheader("Detailed Equipment List")
    
    table_data = []
    for e in equipment_list:
        table_data.append({
            'ID': e.get('id'),
            'Type': e.get('type', 'unknown').title(),
            'Status': status_badge(e.get('status', 'unknown')),
            'Failure Prob %': f"{float(e.get('failure_prob', 0))*100:.1f}",
            'RUL (h)': f"{float(e.get('rul_hours', 0)):.1f}",
            'Last Update': format_timestamp(e.get('last_updated', 'N/A')),
        })
    
    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True)
    
    st.divider()
    
    # ════════════════════════════════════════════════════════════════
    # RISK SCATTER
    # ════════════════════════════════════════════════════════════════
    
    st.subheader("Risk Assessment Scatter")
    st.caption("Failure Probability vs RUL (bubble size = anomaly score)")
    
    scatter_data = {
        'ID': [e['id'] for e in equipment_list],
        'Failure Prob': [float(e.get('failure_prob', 0)) for e in equipment_list],
        'RUL': [float(e.get('rul_hours', 0)) for e in equipment_list],
        'Anomaly': [float(e.get('anomaly_score', 0.5)) for e in equipment_list],
        'Status': [e.get('status', 'normal') for e in equipment_list],
    }
    
    df_scatter = pd.DataFrame(scatter_data)
    
    fig_scatter = go.Figure()
    
    for status in ['critical', 'warning', 'normal', 'offline']:
        mask = df_scatter['Status'] == status
        color_map = {'critical': '#dc3545', 'warning': '#ffc107', 'normal': '#28a745', 'offline': '#6c757d'}
        
        fig_scatter.add_trace(go.Scatter(
            x=df_scatter.loc[mask, 'Failure Prob'],
            y=df_scatter.loc[mask, 'RUL'],
            mode='markers',
            name=status.title(),
            marker=dict(
                size=df_scatter.loc[mask, 'Anomaly'] * 20,
                color=color_map.get(status, '#6c757d'),
                line=dict(width=1, color='white'),
                opacity=0.7,
            ),
            text=df_scatter.loc[mask, 'ID'],
            hovertemplate='<b>%{text}</b><br>Failure: %{x:.2%}<br>RUL: %{y:.1f}h<extra></extra>',
        ))
    
    fig_scatter.update_layout(
        title="Risk Matrix: Failure Probability vs RUL",
        xaxis_title="Failure Probability",
        yaxis_title="RUL (hours)",
        height=500,
        hovermode='closest',
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.divider()
    
    # Export
    export_df = pd.DataFrame(equipment_list)
    csv_data = export_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Export Fleet Data (CSV)",
        data=csv_data,
        file_name=f"aipms_fleet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__" or st.session_state.get("_running_in_streamlit", False):
    show()
