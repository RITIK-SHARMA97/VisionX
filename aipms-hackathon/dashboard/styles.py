"""
AIPMS Dashboard Styles & Theming
Centralized CSS theme management with configuration-driven colors
"""

import streamlit as st
from dashboard import config


def inject_theme_css() -> None:
    """
    Inject industrial theme CSS into Streamlit app.
    All colors are driven by config.COLORS for easy maintenance.
    """
    css = f"""
    <style>
        :root {{
            --color-critical: {config.COLORS['critical']};
            --color-warning: {config.COLORS['warning']};
            --color-normal: {config.COLORS['normal']};
            --color-offline: {config.COLORS['offline']};
            --color-text-dark: {config.COLORS['text_dark']};
            --color-text-light: {config.COLORS['text_light']};
            --color-bg-light: {config.COLORS['bg_light']};
            --color-border: {config.COLORS['border']};
        }}
        
        /* Status badges */
        .status-badge {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .status-critical {{ 
            color: var(--color-critical); 
            background: rgba(220, 53, 69, 0.1);
        }}
        
        .status-warning {{ 
            color: {config.COLORS['warning']}; 
            background: rgba(255, 193, 7, 0.1);
        }}
        
        .status-normal {{ 
            color: var(--color-normal); 
            background: rgba(40, 167, 69, 0.1);
        }}
        
        .status-offline {{
            color: var(--color-offline);
            background: rgba(108, 117, 125, 0.1);
        }}
        
        /* Metric cards */
        .metric-card {{
            background: var(--color-bg-light);
            border-radius: 8px;
            padding: 16px;
            border-left: 4px solid var(--color-critical);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-card.warning {{
            border-left-color: var(--color-warning);
        }}
        
        .metric-card.normal {{
            border-left-color: var(--color-normal);
        }}
        
        /* Section headers */
        h2, h3 {{
            color: var(--color-text-dark);
            border-bottom: 2px solid var(--color-border);
            padding-bottom: 8px;
        }}
        
        /* Info/warning/error boxes */
        .info-box {{
            background: rgba(0, 102, 204, 0.1);
            border-left: 4px solid {config.COLORS['chart_primary']};
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}
        
        .warning-box {{
            background: rgba(255, 193, 7, 0.1);
            border-left: 4px solid var(--color-warning);
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}
        
        .critical-box {{
            background: rgba(220, 53, 69, 0.1);
            border-left: 4px solid var(--color-critical);
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}
        
        /* Chart container */
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        /* Responsive tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }}
        
        table th {{
            background: var(--color-bg-light);
            color: var(--color-text-dark);
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--color-border);
        }}
        
        table td {{
            padding: 12px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        table tr:hover {{
            background: rgba(0, 0, 0, 0.02);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def get_status_color(status: str) -> str:
    """
    Get color for equipment status.
    
    Args:
        status: Status string ('critical', 'warning', 'normal', 'offline')
    
    Returns:
        Hex color code
    """
    return config.COLORS.get(status, config.COLORS['offline'])


def get_status_emoji(status: str) -> str:
    """
    Get emoji for equipment status.
    
    Args:
        status: Status string ('critical', 'warning', 'normal', 'offline')
    
    Returns:
        Status emoji
    """
    status_emojis = {
        'critical': '🔴',
        'warning': '🟡',
        'normal': '🟢',
        'offline': '⚫',
    }
    return status_emojis.get(status, '❓')


def render_status_badge(status: str, label: str = None) -> str:
    """
    Render HTML status badge (for use with st.markdown with unsafe_allow_html=True).
    
    Args:
        status: Status string ('critical', 'warning', 'normal', 'offline')
        label: Optional label text (default: status.upper())
    
    Returns:
        HTML string
    """
    emoji = get_status_emoji(status)
    label = label or status.upper()
    return f'<span class="status-badge status-{status}">{emoji} {label}</span>'
