"""
AIPMS Dashboard Main Application
Streamlit multi-page dashboard
"""
import streamlit as st
import os
from datetime import datetime


def create_dashboard():
    """Initialize and render the AIPMS dashboard"""
    st.set_page_config(
        page_title="AIPMS Dashboard",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # === Application Header ===
    st.title("⚙️ AIPMS — AI-Driven Predictive Maintenance")
    st.markdown("**BIT Sindri Hackathon 2025 | PS-1: AI & Data Analytics**")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fleet Status", "Loading...", delta="Updating")
    with col2:
        st.metric("Critical Alerts", "0", delta="Real-time")
    with col3:
        st.metric("System Uptime", "Starting", delta="Connected")

    # === Navigation Sidebar ===
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Fleet Overview", "Equipment Detail", "KPI Dashboard", "Schedule", "Alert Feed"]
    )

    st.sidebar.divider()

    st.sidebar.write("### System Info")
    st.sidebar.info(
        f"""
        **Status**: Initializing  
        **API**: http://localhost:8000  
        **Dashboard**: Running  
        **Time**: {datetime.now().strftime('%H:%M:%S')}
        """
    )

    # === Page Router ===
    st.write(f"## {page}")
    st.info(f"Page '{page}' will be implemented in Phase 5 (Streamlit Dashboard)")


if __name__ == "__main__":
    create_dashboard()

# === Placeholder Content ===
with st.expander("ℹ️ About AIPMS"):
    st.markdown("""
    AIPMS (AI-Driven Predictive Maintenance System) is a full-stack solution for mining equipment health prediction.
    
    **Key Components**:
    - 📊 Real-time sensor data via MQTT
    - 🤖 ML models: Anomaly Detection, Failure Prediction, RUL Estimation
    - ⚡ FastAPI backend with high-performance inference
    - 📈 Interactive Streamlit dashboard with alerts and scheduling
    
    **Timeline**: 36-hour implementation (April 2025)
    """)

st.divider()
st.caption("AIPMS v0.1.0 | Phase 1: Setup Complete ✅ | Next: Phase 2A & 2B (IoT + ML Prep)")
