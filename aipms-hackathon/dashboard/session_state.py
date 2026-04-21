"""
AIPMS Dashboard Session State Management
Centralized, typed state management for multi-page Streamlit app
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import streamlit as st
import logging

logger = logging.getLogger(__name__)


@dataclass
class DashboardState:
    """
    Application state schema with validation.
    Single source of truth for all session state.
    """
    # Navigation
    selected_equipment: Optional[str] = None
    
    # Timing
    last_refresh: Optional[datetime] = None
    refresh_interval_seconds: int = 5
    
    # API Status
    api_status: str = "unknown"  # ok, degraded, down, unknown
    last_api_error: Optional[str] = None
    
    # User
    user_id: str = "demo_user"
    
    # Filters & Options
    alert_filter_severity: List[str] = field(default_factory=lambda: ["critical", "warning"])
    alert_filter_acknowledged: Optional[bool] = None  # None = show all
    maintenance_days_ahead: int = 7
    
    # Cache
    _equipment_list_cache: Optional[List[Dict]] = field(default=None, repr=False)
    _last_cache_update: Optional[datetime] = field(default=None, repr=False)


def get_state() -> DashboardState:
    """
    Get current dashboard state (singleton pattern).
    
    Returns:
        DashboardState instance
    """
    if '_aipms_state' not in st.session_state:
        st.session_state._aipms_state = DashboardState()
        logger.debug("Initialized new DashboardState")
    return st.session_state._aipms_state


def set_equipment(equipment_id: str) -> None:
    """
    Set selected equipment with validation.
    
    Args:
        equipment_id: Equipment ID string
    
    Raises:
        ValueError: If equipment_id is invalid
    """
    if not isinstance(equipment_id, str) or not equipment_id.strip():
        raise ValueError(f"Invalid equipment_id: {equipment_id}")
    
    state = get_state()
    state.selected_equipment = equipment_id
    logger.debug(f"Selected equipment: {equipment_id}")


def update_api_status(status: str, error: Optional[str] = None) -> None:
    """
    Update API health status.
    
    Args:
        status: Status string ('ok', 'degraded', 'down', 'unknown')
        error: Optional error message
    """
    valid_statuses = ['ok', 'degraded', 'down', 'unknown']
    if status not in valid_statuses:
        logger.warning(f"Invalid API status: {status}")
        status = 'unknown'
    
    state = get_state()
    state.api_status = status
    state.last_api_error = error
    state.last_refresh = datetime.now()
    
    logger.debug(f"API status updated: {status}" + (f" - {error}" if error else ""))


def get_api_status_emoji() -> str:
    """
    Get emoji for current API status.
    
    Returns:
        Status emoji
    """
    state = get_state()
    status_emojis = {
        'ok': '🟢',
        'degraded': '🟡',
        'down': '🔴',
        'unknown': '⚫',
    }
    return status_emojis.get(state.api_status, '❓')


def is_api_ready() -> bool:
    """
    Check if API is ready for requests.
    
    Returns:
        True if API status is 'ok', False otherwise
    """
    state = get_state()
    return state.api_status == 'ok'


def cache_equipment_list(equipment_list: List[Dict]) -> None:
    """
    Cache equipment list in session state (1 minute TTL).
    
    Args:
        equipment_list: List of equipment dictionaries
    """
    state = get_state()
    state._equipment_list_cache = equipment_list
    state._last_cache_update = datetime.now()
    logger.debug(f"Cached equipment list: {len(equipment_list)} items")


def get_cached_equipment_list(max_age_seconds: int = 60) -> Optional[List[Dict]]:
    """
    Get cached equipment list if still fresh.
    
    Args:
        max_age_seconds: Maximum cache age in seconds (default 60)
    
    Returns:
        Cached equipment list or None if expired/missing
    """
    state = get_state()
    
    if state._equipment_list_cache is None or state._last_cache_update is None:
        return None
    
    age = (datetime.now() - state._last_cache_update).total_seconds()
    if age > max_age_seconds:
        logger.debug(f"Equipment cache expired (age: {age}s)")
        return None
    
    logger.debug(f"Using cached equipment list (age: {age:.1f}s)")
    return state._equipment_list_cache


def clear_state() -> None:
    """
    Clear all session state (useful for logout or reset).
    """
    if '_aipms_state' in st.session_state:
        del st.session_state._aipms_state
    logger.debug("Session state cleared")


def reset_equipment_selection() -> None:
    """Reset selected equipment to None."""
    state = get_state()
    state.selected_equipment = None
    logger.debug("Equipment selection reset")
