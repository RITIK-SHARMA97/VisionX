"""
AIPMS Dashboard Chart Components
Reusable Plotly chart builders for consistent visualizations
"""

import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dashboard.config import COLORS, CHART_CONFIG, THRESHOLDS

# ============================================================================
# SENSOR TREND CHARTS
# ============================================================================

def create_sensor_trend_chart(
    sensor_data: List[Dict],
    sensor_name: str,
    unit: str,
    threshold_warning: Optional[float] = None,
    threshold_critical: Optional[float] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Create a sensor trend chart with threshold indicators.
    
    Args:
        sensor_data: List of {timestamp, value} dicts
        sensor_name: Name of the sensor
        unit: Unit of measurement (°C, mm/s, bar, etc.)
        threshold_warning: Warning threshold line
        threshold_critical: Critical threshold line
        title: Chart title
    
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(sensor_data)
    
    if df.empty:
        return _create_empty_chart(f"No data for {sensor_name}")
    
    # Sort by timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    fig = go.Figure()
    
    # Main sensor line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['value'],
        mode='lines',
        name=sensor_name,
        line=dict(color=COLORS['chart_primary'], width=3),
        hovertemplate='<b>%{x|%H:%M:%S}</b><br>' + f'{sensor_name}: %{{y:.2f}} {unit}<extra></extra>',
        fill='tozeroy',
        fillcolor='rgba(0, 102, 204, 0.1)',
    ))
    
    # Warning threshold
    if threshold_warning is not None:
        fig.add_hline(
            y=threshold_warning,
            line_dash='dash',
            line_color=COLORS['warning'],
            annotation_text='⚠️ Warning',
            annotation_position='right',
        )
    
    # Critical threshold
    if threshold_critical is not None:
        fig.add_hline(
            y=threshold_critical,
            line_dash='solid',
            line_color=COLORS['critical'],
            annotation_text='🔴 Critical',
            annotation_position='right',
        )
    
    # Layout
    fig.update_layout(
        title=title or f'{sensor_name} Trend ({unit})',
        xaxis_title='Time',
        yaxis_title=f'{sensor_name} ({unit})',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        **CHART_CONFIG,
    )
    
    return fig


def create_multi_sensor_chart(
    sensor_dict: Dict[str, List[Dict]],
    title: str = 'Multi-Sensor Trends',
) -> go.Figure:
    """
    Create a multi-sensor trend chart on one axis.
    
    Args:
        sensor_dict: {sensor_name: [{timestamp, value}, ...]}
        title: Chart title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    colors_list = [
        COLORS['chart_primary'],
        COLORS['chart_secondary'],
        COLORS['chart_danger'],
        COLORS['warning'],
    ]
    
    for idx, (sensor_name, data) in enumerate(sensor_dict.items()):
        df = pd.DataFrame(data)
        if df.empty:
            continue
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['value'],
            mode='lines',
            name=sensor_name,
            line=dict(
                color=colors_list[idx % len(colors_list)],
                width=2,
            ),
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Value (normalized)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        **CHART_CONFIG,
    )
    
    return fig


# ============================================================================
# RUL DEGRADATION CHART
# ============================================================================

def create_rul_degradation_chart(
    rul_history: List[Dict],
    equipment_id: str,
) -> go.Figure:
    """
    Create RUL degradation chart with confidence intervals.
    
    Args:
        rul_history: List of {timestamp, rul_hours, rul_low, rul_high}
        equipment_id: Equipment identifier
    
    Returns:
        Plotly figure with shaded confidence interval
    """
    df = pd.DataFrame(rul_history)
    
    if df.empty:
        return _create_empty_chart(f"No RUL history for {equipment_id}")
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    fig = go.Figure()
    
    # Confidence interval (shaded band)
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['rul_high'],
        fill=None,
        mode='lines',
        line_color='rgba(0, 0, 0, 0)',
        showlegend=False,
        name='Upper Bound',
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['rul_low'],
        fill='tonexty',
        mode='lines',
        line_color='rgba(0, 0, 0, 0)',
        showlegend=False,
        name='Lower Bound',
        fillcolor='rgba(107, 174, 214, 0.2)',  # Light blue shading
    ))
    
    # Main RUL line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['rul_hours'],
        mode='lines+markers',
        name='Remaining Useful Life',
        line=dict(color=COLORS['chart_primary'], width=3),
        marker=dict(size=6),
        hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>' +
                     f'RUL: %{{y:.1f}} hours<br>' +
                     f'95% CI: [%{{customdata[0]:.1f}}, %{{customdata[1]:.1f}}]<extra></extra>',
        customdata=df[['rul_low', 'rul_high']].values,
    ))
    
    # Critical threshold (48 hours)
    fig.add_hline(
        y=THRESHOLDS['rul_hours']['critical'],
        line_dash='solid',
        line_color=COLORS['critical'],
        annotation_text='🔴 Critical (48h)',
        annotation_position='right',
    )
    
    # Warning threshold (168 hours / 1 week)
    fig.add_hline(
        y=THRESHOLDS['rul_hours']['warning'],
        line_dash='dash',
        line_color=COLORS['warning'],
        annotation_text='⚠️ Warning (1 week)',
        annotation_position='right',
    )
    
    fig.update_layout(
        title=f'RUL Degradation - {equipment_id}',
        xaxis_title='Time',
        yaxis_title='Remaining Useful Life (hours)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        **CHART_CONFIG,
    )
    
    return fig


# ============================================================================
# SHAP FEATURE ATTRIBUTION
# ============================================================================

def create_shap_bar_chart(
    shap_data: List[Dict],
    equipment_id: str,
) -> go.Figure:
    """
    Create horizontal bar chart for SHAP feature attribution.
    
    Args:
        shap_data: List of {sensor, shap_value, impact_pct}
        equipment_id: Equipment identifier
    
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(shap_data)
    
    if df.empty:
        return _create_empty_chart("No attribution data")
    
    # Sort by absolute value descending
    df = df.sort_values('shap_value', ascending=True)
    
    fig = go.Figure()
    
    # Color bars based on positive/negative contribution
    colors = [
        COLORS['chart_danger'] if x < 0 else COLORS['chart_success']
        for x in df['shap_value']
    ]
    
    fig.add_trace(go.Bar(
        y=df['sensor'],
        x=df['shap_value'],
        orientation='h',
        marker=dict(color=colors),
        text=df['impact_pct'].apply(lambda x: f'{x:.0f}%'),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>SHAP: %{x:.3f}<br>Impact: %{text}%<extra></extra>',
    ))
    
    fig.update_layout(
        title=f'Feature Attribution (SHAP) - {equipment_id}',
        xaxis_title='SHAP Value',
        yaxis_title='Sensor / Feature',
        height=400,
        showlegend=False,
        **CHART_CONFIG,
    )
    
    return fig


# ============================================================================
# GANTT TIMELINE
# ============================================================================

def create_maintenance_gantt(
    schedule_data: List[Dict],
) -> go.Figure:
    """
    Create Gantt timeline for maintenance schedule.
    
    Args:
        schedule_data: List of {equipment_id, start, end, priority, action}
        priority: 'critical' | 'warning' | 'routine'
    
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(schedule_data)
    
    if df.empty:
        return _create_empty_chart("No scheduled maintenance")
    
    # Map priority to color
    priority_colors = {
        'critical': COLORS['critical'],
        'warning': COLORS['warning'],
        'routine': COLORS['normal'],
    }
    
    df['color'] = df['priority'].map(priority_colors)
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    
    fig = px.timeline(
        df,
        x_start='start',
        x_end='end',
        y='equipment_id',
        color='priority',
        hover_data=['action'],
        color_discrete_map=priority_colors,
        title='7-Day Maintenance Schedule',
        labels={'equipment_id': 'Equipment', 'priority': 'Priority'},
    )
    
    fig.update_layout(
        height=400,
        xaxis_title='Timeline',
        yaxis_title='Equipment',
        template='plotly_white',
        **CHART_CONFIG,
    )
    
    return fig


# ============================================================================
# RISK HEATMAP
# ============================================================================

def create_fleet_risk_heatmap(
    equipment_list: List[Dict],
) -> go.Figure:
    """
    Create equipment risk heatmap (failure probability grid).
    
    Args:
        equipment_list: List of {equipment_id, failure_prob, anomaly_score}
    
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(equipment_list)
    
    if df.empty:
        return _create_empty_chart("No equipment data")
    
    # Create a 2D array: failure_prob vs anomaly_score
    fig = go.Figure(data=go.Scatter(
        x=df['anomaly_score'],
        y=df['failure_prob'],
        mode='markers',
        marker=dict(
            size=15,
            color=df['failure_prob'],
            colorscale='RdYlGn_r',  # Red (high risk) to Green (low risk)
            showscale=True,
            colorbar=dict(title='Failure<br>Probability'),
            line=dict(
                color='white',
                width=2,
            ),
        ),
        text=df['equipment_id'],
        hovertemplate='<b>%{text}</b><br>' +
                     'Anomaly Score: %{x:.2f}<br>' +
                     'Failure Prob: %{y:.2f}<extra></extra>',
    ))
    
    # Critical zone shading
    fig.add_vrect(
        x0=THRESHOLDS['anomaly_score']['warning'],
        x1=1.0,
        fillcolor=COLORS['warning'],
        opacity=0.1,
        layer='below',
        line_width=0,
    )
    
    fig.add_hrect(
        y0=THRESHOLDS['failure_prob']['warning'],
        y1=1.0,
        fillcolor=COLORS['critical'],
        opacity=0.1,
        layer='below',
        line_width=0,
    )
    
    fig.update_layout(
        title='Fleet Risk Assessment',
        xaxis_title='Anomaly Score',
        yaxis_title='Failure Probability',
        height=450,
        template='plotly_white',
        **CHART_CONFIG,
    )
    
    return fig


# ============================================================================
# STATUS DISTRIBUTION PIE/DONUT
# ============================================================================

def create_fleet_status_distribution(
    status_counts: Dict[str, int],
) -> go.Figure:
    """
    Create pie chart of fleet status distribution.
    
    Args:
        status_counts: {status: count} ('critical', 'warning', 'normal', 'offline')
    
    Returns:
        Plotly figure
    """
    status_colors = {
        'critical': COLORS['critical'],
        'warning': COLORS['warning'],
        'normal': COLORS['normal'],
        'offline': COLORS['offline'],
    }
    
    labels = list(status_counts.keys())
    values = list(status_counts.values())
    colors = [status_colors.get(label, '#999') for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>',
        textposition='inside',
        textinfo='label+percent',
    )])
    
    fig.update_layout(
        title='Fleet Status Distribution',
        height=400,
        **CHART_CONFIG,
    )
    
    return fig


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _create_empty_chart(message: str) -> go.Figure:
    """Create a placeholder chart for empty data."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref='paper',
        yref='paper',
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color=COLORS['text_muted']),
    )
    fig.update_layout(
        height=400,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        template='plotly_white',
    )
    return fig
