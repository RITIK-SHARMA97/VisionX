"""
AIPMS Dashboard Configuration
Color palette, thresholds, and visual settings
"""

# Color Palette - Industrial + Professional
COLORS = {
    # Status indicators
    'critical': '#dc3545',      # Red - immediate action required
    'warning': '#ffc107',       # Amber - caution, monitor closely
    'normal': '#28a745',        # Green - healthy
    'offline': '#6c757d',       # Gray - offline
    
    # UI backgrounds
    'bg_light': '#f8f9fa',      # Light background
    'bg_card': '#ffffff',       # Card background
    'border': '#dee2e6',        # Border color
    
    # Text
    'text_dark': '#212529',     # Dark text
    'text_light': '#6c757d',    # Light text
    'text_muted': '#adb5bd',    # Muted text
    
    # Charts
    'chart_primary': '#0066cc',     # Primary chart color
    'chart_secondary': '#6c63ff',   # Secondary
    'chart_danger': '#dc3545',      # Danger series
    'chart_warning': '#ffc107',     # Warning series
    'chart_success': '#28a745',     # Success series
    'chart_grid': '#e9ecef',        # Grid lines
}

# Thresholds for status indicators
THRESHOLDS = {
    'failure_prob': {
        'critical': 0.70,      # >= 70% probability = critical
        'warning': 0.50,       # >= 50% probability = warning
        'normal': 0.00,        # < 50% probability = normal
    },
    'anomaly_score': {
        'critical': 0.70,
        'warning': 0.40,
        'normal': 0.00,
    },
    'rul_hours': {
        'critical': 48,        # < 48 hours = critical
        'warning': 168,        # < 168 hours (1 week) = warning
    },
}

# Equipment type icons and colors
EQUIPMENT_TYPES = {
    'excavator': {
        'icon': '⛏️',
        'label': 'Rope Shovel',
        'color': '#ff6b6b',
    },
    'dumper': {
        'icon': '🚛',
        'label': 'Rear Dump Truck',
        'color': '#4ecdc4',
    },
    'conveyor': {
        'icon': '📦',
        'label': 'Belt Conveyor',
        'color': '#ffd93d',
    },
    'drill': {
        'icon': '🔩',
        'label': 'Rotary Drill',
        'color': '#a8dadc',
    },
}

# Chart styling defaults
CHART_CONFIG = {
    'plot_bgcolor': 'rgba(248, 249, 250, 1)',  # Light background
    'paper_bgcolor': 'white',
    'hovermode': 'x unified',
    'font': {
        'family': 'Arial, sans-serif',
        'size': 12,
        'color': '#212529',
    },
    'margin': {
        'l': 50,
        'r': 20,
        't': 40,
        'b': 50,
    },
}

# API Configuration
API_CONFIG = {
    'base_url': 'http://localhost:8000',
    'timeout': 5.0,
    'retry_count': 2,
}

# Dashboard refresh settings
REFRESH_CONFIG = {
    'interval_seconds': 5,
    'poll_interval': 5,
}

# Time period defaults
TIME_PERIODS = {
    'last_10_min': 10,
    'last_1_hour': 60,
    'last_6_hours': 360,
    'last_24_hours': 1440,
    'last_7_days': 10080,
}

# Maintenance schedule settings
SCHEDULE_CONFIG = {
    'forecast_days': 7,
    'priority_tiers': {
        'critical': {
            'window': 24,  # hours
            'color': COLORS['critical'],
        },
        'warning': {
            'window': 72,  # hours
            'color': COLORS['warning'],
        },
        'routine': {
            'window': 168,  # hours (1 week)
            'color': COLORS['normal'],
        },
    },
}

# Export settings
EXPORT_CONFIG = {
    'formats': ['CSV', 'JSON'],
    'timestamp_format': '%Y-%m-%d %H:%M:%S',
}
