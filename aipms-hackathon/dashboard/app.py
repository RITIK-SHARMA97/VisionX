"""
AIPMS Dashboard - Multi-Page Navigation Hub
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 5.2-5.5: Enhanced Dashboard with Plotly Visualizations
- Multi-page Streamlit architecture (pages/ folder)
- Plotly charts: sensor trends, RUL degradation, SHAP attribution
- Gantt timeline for maintenance schedule
- Fleet risk heatmap
- Advanced filtering & CSV export

Design: Industrial + Data-Driven
  - Answers key operator questions: Is it healthy? What changed? What to do?
  - Color-coded status badges with semantic meaning
  - Real-time refresh with configurable intervals
"""

import sys
from pathlib import Path

# Fix module path - add aipms-hackathon directory to sys.path
dashboard_dir = Path(__file__).parent.parent.absolute()
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

import streamlit as st
import logging
from datetime import datetime
from dashboard import config
from dashboard.styles import inject_theme_css
from dashboard.session_state import get_state, set_equipment, update_api_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.debug("Dashboard initialization started")

# ═════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title='AIPMS Dashboard - Phase 5',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

# Guard: Only run dashboard logic if executed via streamlit
def run_dashboard():
    """Main dashboard application logic - only runs when executed via streamlit."""
    
    # Inject theme CSS from centralized styles
    inject_theme_css()

    # ═════════════════════════════════════════════════════════════════
    # SESSION STATE (Centralized)
    # ═════════════════════════════════════════════════════════════════

    state = get_state()  # Initialize centralized state

    # ═════════════════════════════════════════════════════════════════
    # HEADER
    # ═════════════════════════════════════════════════════════════════

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("## ⛏️ AIPMS")
        st.markdown("**AI-Powered Maintenance**")

    with col2:
        st.markdown("")

    with col3:
        status_emoji = get_state().api_status
        emoji_map = {
            'ok': '🟢',
            'degraded': '🟡',
            'down': '🔴',
            'unknown': '⚫',
        }
        emoji = emoji_map.get(get_state().api_status, '⚫')
        st.markdown(f"**Status**: {emoji} {get_state().api_status.upper()}")
        if get_state().last_refresh:
            st.caption(f"Last update: {get_state().last_refresh.strftime('%H:%M:%S')}")

    st.divider()

    # ═════════════════════════════════════════════════════════════════
    # SIDEBAR NAVIGATION
    # ═════════════════════════════════════════════════════════════════

    st.sidebar.markdown("## 🏭 AIPMS Dashboard")

    page = st.sidebar.radio(
        "Navigate",
        options=[
            "⚙️ Fleet Overview",
            "🔍 Equipment Detail",
            "📋 Maintenance Schedule",
            "⚠️ Alert Feed",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    with st.sidebar:
        st.markdown("### Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("📥 Export", use_container_width=True):
                st.info("Export on individual pages")
        
        st.divider()
        
        st.markdown("### About")
        st.caption("""
            **AIPMS Dashboard v2.0**
            
            Multi-page Edition with Plotly
            
            Predictive maintenance for coal mining equipment.
            
            Built with Streamlit + Plotly + FastAPI
        """)

    # ═════════════════════════════════════════════════════════════════
    # PAGE ROUTING (Manual for backward compatibility)
    # ═════════════════════════════════════════════════════════════════

    # Import page modules
    try:
        from pages import fleet_overview, equipment_detail, maintenance_schedule, alert_feed, kpi_dashboard
    except ImportError as e:
        logger.error(f"Failed to import page modules: {e}")
        st.error(f"❌ Failed to load dashboard pages: {e}")
        fleet_overview = None
        equipment_detail = None
        maintenance_schedule = None
        alert_feed = None
        kpi_dashboard = None

    try:
        if page == "⚙️ Fleet Overview":
            if fleet_overview and hasattr(fleet_overview, 'show'):
                try:
                    fleet_overview.show()
                except Exception as e:
                    st.error(f"❌ Error loading Fleet Overview: {e}")
                    logger.error(f"Fleet Overview page error: {e}", exc_info=True)
            else:
                st.info("⚙️ Fleet Overview page not yet implemented")
        
        elif page == "🔍 Equipment Detail":
            if equipment_detail and hasattr(equipment_detail, 'show'):
                try:
                    equipment_detail.show()
                except Exception as e:
                    st.error(f"❌ Error loading Equipment Detail: {e}")
                    logger.error(f"Equipment Detail page error: {e}", exc_info=True)
            else:
                st.info("🔍 Equipment Detail page not yet implemented")
        
        elif page == "📋 Maintenance Schedule":
            if maintenance_schedule and hasattr(maintenance_schedule, 'show'):
                try:
                    maintenance_schedule.show()
                except Exception as e:
                    st.error(f"❌ Error loading Maintenance Schedule: {e}")
                    logger.error(f"Maintenance Schedule page error: {e}", exc_info=True)
            else:
                st.info("📋 Maintenance Schedule page not yet implemented")
        
        elif page == "⚠️ Alert Feed":
            if alert_feed and hasattr(alert_feed, 'show'):
                try:
                    alert_feed.show()
                except Exception as e:
                    st.error(f"❌ Error loading Alert Feed: {e}")
                    logger.error(f"Alert Feed page error: {e}", exc_info=True)
            else:
                st.info("⚠️ Alert Feed page not yet implemented")
        
        else:
            st.warning(f"Unknown page: {page}")

    except Exception as e:
        st.error(f"❌ Fatal error in page routing: {e}")
        logger.exception("Unhandled exception in page routing")

    # ═════════════════════════════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════════════════════════════

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("📍 Dhanbad, Jharkhand")

    with col2:
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

    with col3:
        st.caption("🔐 Local Data - No External APIs")


# Only run dashboard if executed directly via streamlit run
# Skip module-level execution to allow imports without session state errors
if __name__ == "__main__":
    try:
        run_dashboard()
    except Exception as e:
        logger.error(f"Dashboard execution failed: {e}", exc_info=True)


# ═════════════════════════════════════════════════════════════════
# IMPORTABLE DASHBOARD FACTORY FUNCTION (for testing)
# ═════════════════════════════════════════════════════════════════

def create_dashboard():
    """
    Factory function to create and configure the dashboard.
    Allows the dashboard to be imported and tested programmatically.
    
    Returns:
        None (runs the dashboard directly when called in streamlit context)
    """
    run_dashboard()
