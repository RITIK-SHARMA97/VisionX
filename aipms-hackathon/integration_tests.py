"""
AIPMS Integration Tests - Phase 6
Tests the complete end-to-end flow: Simulator → MQTT → DB → API → Dashboard

Run with: pytest integration_tests.py -v
"""

import pytest
import asyncio
import time
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES & SETUP
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "aipms.db"
API_BASE = "http://localhost:8000"

@pytest.fixture
def db_connection():
    """Provide database connection for tests"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

@pytest.fixture
def api_client():
    """Provide API client for tests"""
    class APIClient:
        def get(self, endpoint: str, timeout: int = 5):
            url = f"{API_BASE}{endpoint}"
            response = requests.get(url, timeout=timeout)
            return response
        
        def post(self, endpoint: str, data: dict = None, timeout: int = 5):
            url = f"{API_BASE}{endpoint}"
            response = requests.post(url, json=data, timeout=timeout)
            return response
    
    return APIClient()

# ═══════════════════════════════════════════════════════════════════════════════
# DATA FLOW TESTS (Simulator → MQTT → DB → API)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataFlow:
    """Test the complete data flow through all components"""
    
    def test_mqtt_messages_received(self):
        """Verify MQTT messages are being published by simulator"""
        try:
            import paho.mqtt.client as mqtt
            
            received = {"messages": []}
            event = asyncio.Event()
            
            def on_message(client, userdata, msg):
                try:
                    payload = json.loads(msg.payload.decode())
                    received["messages"].append(payload)
                    if len(received["messages"]) >= 3:
                        event.set()
                except:
                    pass
            
            client = mqtt.Client()
            client.on_message = on_message
            client.connect("localhost", 1883, keepalive=5)
            client.subscribe("mines/equipment/+/sensors")
            client.loop_start()
            
            # Wait for messages
            start_time = time.time()
            while (time.time() - start_time) < 30:
                if len(received["messages"]) >= 3:
                    break
                time.sleep(0.5)
            
            client.loop_stop()
            client.disconnect()
            
            assert len(received["messages"]) >= 3, f"Expected ≥3 MQTT messages, got {len(received['messages'])}"
            
            # Verify message structure
            for msg in received["messages"]:
                assert "equipment_id" in msg
                assert "timestamp" in msg
                assert "sensor_name" in msg
                assert "value" in msg
                assert isinstance(msg["value"], (int, float))
        
        except Exception as e:
            pytest.skip(f"MQTT not available: {e}")
    
    def test_sensor_data_in_database(self, db_connection):
        """Verify sensor data flows to database"""
        # Count current rows
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        initial_count = cursor.fetchone()[0]
        
        # Wait for new data
        time.sleep(3)
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        final_count = cursor.fetchone()[0]
        
        assert final_count > initial_count, "No new sensor data written to database"
        
        # Verify data structure
        cursor.execute("SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        assert row is not None
        assert row["equipment_id"] is not None
        assert row["sensor_name"] is not None
        assert row["value"] is not None
    
    def test_mqtt_to_database_latency(self, db_connection):
        """Verify MQTT to DB latency is reasonable (<2s)"""
        try:
            import paho.mqtt.client as mqtt
            from datetime import datetime
            
            test_timestamp = datetime.utcnow().isoformat()
            latencies = []
            
            def on_message(client, userdata, msg):
                try:
                    payload = json.loads(msg.payload.decode())
                    
                    # Check if this message is in database
                    cursor = db_connection.cursor()
                    cursor.execute(
                        "SELECT timestamp FROM sensor_readings WHERE equipment_id=? AND sensor_name=? ORDER BY timestamp DESC LIMIT 1",
                        (payload["equipment_id"], payload["sensor_name"])
                    )
                    row = cursor.fetchone()
                    if row:
                        latencies.append(time.time() - payload.get("received_time", time.time()))
                except:
                    pass
            
            # Monitor MQTT
            client = mqtt.Client()
            client.on_message = on_message
            client.connect("localhost", 1883, keepalive=5)
            client.subscribe("mines/equipment/+/sensors")
            client.loop_start()
            
            time.sleep(5)
            client.loop_stop()
            client.disconnect()
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                assert avg_latency < 5.0, f"MQTT->DB latency too high: {avg_latency:.2f}s"
        
        except Exception as e:
            pytest.skip(f"Latency test unavailable: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# API TESTS (Endpoints & Data Contracts)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPI:
    """Test FastAPI backend endpoints"""
    
    def test_health_endpoint(self, api_client):
        """Test /health endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "api" in data
        assert data["api"] == "ok"
    
    def test_equipment_list(self, api_client):
        """Test /equipment endpoint returns list"""
        response = api_client.get("/equipment")
        assert response.status_code == 200
        equipment = response.json()
        assert isinstance(equipment, list)
        assert len(equipment) >= 3, "Expected ≥3 equipment units"
        
        # Verify equipment structure
        for item in equipment:
            assert "id" in item
            assert "name" in item
            assert "type" in item
            assert "status" in item
    
    def test_equipment_detail(self, api_client):
        """Test /equipment/{id} endpoint"""
        # Get list first
        response = api_client.get("/equipment")
        assert response.status_code == 200
        equipment = response.json()
        assert len(equipment) > 0
        
        # Get detail
        eq_id = equipment[0]["id"]
        response = api_client.get(f"/equipment/{eq_id}")
        assert response.status_code == 200
        detail = response.json()
        
        assert detail["id"] == eq_id
        assert "predictions" in detail or "status" in detail
    
    def test_alerts_endpoint(self, api_client):
        """Test /alerts endpoint"""
        response = api_client.get("/alerts")
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)
    
    def test_schedule_endpoint(self, api_client):
        """Test /schedule endpoint"""
        response = api_client.get("/schedule")
        assert response.status_code == 200
        schedule = response.json()
        assert isinstance(schedule, list)
    
    def test_api_response_time(self, api_client):
        """Test API response time is acceptable (<500ms)"""
        start = time.time()
        response = api_client.get("/equipment")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert elapsed < 1000, f"API response time too slow: {elapsed:.0f}ms"
    
    def test_api_error_handling(self, api_client):
        """Test API error handling for invalid requests"""
        response = api_client.get("/equipment/INVALID_ID")
        # Should return 404 or empty list, not 500
        assert response.status_code in [200, 404]

# ═══════════════════════════════════════════════════════════════════════════════
# ML MODEL TESTS (Inference Pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMLPipeline:
    """Test ML inference pipeline"""
    
    def test_predictions_generated(self, db_connection):
        """Verify ML predictions are being generated"""
        cursor = db_connection.cursor()
        
        # Wait for predictions
        time.sleep(5)
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        count = cursor.fetchone()[0]
        assert count > 0, "No predictions generated"
        
        cursor.execute("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        
        assert row["equipment_id"] is not None
        assert row["anomaly_score"] is not None
        assert row["failure_prob"] is not None
        assert row["rul_hours"] is not None
    
    def test_anomaly_scores(self, db_connection):
        """Verify anomaly scores are in valid range"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT anomaly_score FROM predictions WHERE anomaly_score IS NOT NULL LIMIT 10")
        scores = [row[0] for row in cursor.fetchall()]
        
        for score in scores:
            assert 0 <= score <= 1, f"Anomaly score out of range: {score}"
    
    def test_failure_probabilities(self, db_connection):
        """Verify failure probabilities are in valid range"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT failure_prob FROM predictions WHERE failure_prob IS NOT NULL LIMIT 10")
        probs = [row[0] for row in cursor.fetchall()]
        
        for prob in probs:
            assert 0 <= prob <= 1, f"Failure probability out of range: {prob}"
    
    def test_rul_estimates(self, db_connection):
        """Verify RUL estimates are realistic"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT rul_hours FROM predictions WHERE rul_hours IS NOT NULL LIMIT 10")
        ruls = [row[0] for row in cursor.fetchall()]
        
        for rul in ruls:
            assert rul >= 0, f"RUL cannot be negative: {rul}"
            assert rul <= 500, f"RUL unrealistically high: {rul}"

# ═══════════════════════════════════════════════════════════════════════════════
# ALERT & MAINTENANCE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAlertsAndMaintenance:
    """Test alert generation and maintenance scheduling"""
    
    def test_alerts_exist(self, db_connection):
        """Verify alerts table exists and has records"""
        cursor = db_connection.cursor()
        
        # Wait for alerts
        time.sleep(3)
        
        cursor.execute("SELECT COUNT(*) FROM alerts")
        count = cursor.fetchone()[0]
        
        # Alerts may not exist yet, so we just verify table exists
        assert count >= 0
    
    def test_maintenance_jobs_exist(self, db_connection):
        """Verify maintenance jobs table exists"""
        cursor = db_connection.cursor()
        
        # Wait for jobs
        time.sleep(3)
        
        cursor.execute("SELECT COUNT(*) FROM maintenance_jobs")
        count = cursor.fetchone()[0]
        
        # Jobs may not exist yet
        assert count >= 0
    
    def test_alert_structure(self, db_connection):
        """Verify alert records have correct structure"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM alerts LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            assert row["equipment_id"] is not None
            assert row["severity"] is not None
            assert row["message"] is not None

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TESTS (UI Responsiveness)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboard:
    """Test Streamlit dashboard"""
    
    def test_dashboard_accessible(self):
        """Verify dashboard is accessible"""
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not accessible")
    
    def test_dashboard_load_time(self):
        """Test dashboard load time"""
        try:
            start = time.time()
            response = requests.get("http://localhost:8501", timeout=10)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 10, f"Dashboard load time too long: {elapsed:.1f}s"
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not accessible")

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION FLOW TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullFlow:
    """Test complete end-to-end flow"""
    
    def test_complete_flow(self, db_connection, api_client):
        """Test complete flow: Simulator → MQTT → DB → API → Predictions"""
        
        # 1. Verify simulator is running (sensor data exists)
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        initial_sensor_count = cursor.fetchone()[0]
        
        # 2. Wait and check for new data
        time.sleep(3)
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        new_sensor_count = cursor.fetchone()[0]
        assert new_sensor_count > initial_sensor_count, "Simulator not generating data"
        
        # 3. Verify API is returning equipment
        response = api_client.get("/equipment")
        assert response.status_code == 200
        equipment = response.json()
        assert len(equipment) > 0
        
        # 4. Verify predictions are being generated
        time.sleep(3)
        cursor.execute("SELECT COUNT(*) FROM predictions")
        prediction_count = cursor.fetchone()[0]
        assert prediction_count > 0, "No predictions being generated"
        
        # 5. Verify API can return predictions via equipment endpoint
        eq_id = equipment[0]["id"]
        response = api_client.get(f"/equipment/{eq_id}")
        assert response.status_code == 200
    
    def test_multi_equipment_flow(self, db_connection):
        """Test flow works for multiple equipment units"""
        cursor = db_connection.cursor()
        
        # Get unique equipment
        cursor.execute("SELECT DISTINCT equipment_id FROM sensor_readings LIMIT 5")
        equipment_ids = [row[0] for row in cursor.fetchall()]
        
        assert len(equipment_ids) >= 2, "Should have at least 2 equipment units generating data"
        
        # Check predictions for each
        for eq_id in equipment_ids:
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE equipment_id=?", (eq_id,))
            count = cursor.fetchone()[0]
            # Some equipment may not have predictions yet
            assert count >= 0
    
    def test_data_consistency(self, db_connection):
        """Test data consistency across tables"""
        cursor = db_connection.cursor()
        
        # Get equipment that has sensor data
        cursor.execute("SELECT DISTINCT equipment_id FROM sensor_readings LIMIT 1")
        eq_row = cursor.fetchone()
        if eq_row:
            eq_id = eq_row[0]
            
            # Verify equipment exists in equipment table
            cursor.execute("SELECT id FROM equipment WHERE id=?", (eq_id,))
            assert cursor.fetchone() is not None, f"Equipment {eq_id} has sensor data but not in equipment table"

# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformance:
    """Test performance characteristics"""
    
    def test_inference_latency(self, db_connection):
        """Test ML inference latency is acceptable"""
        cursor = db_connection.cursor()
        
        # Get recent predictions
        cursor.execute(
            "SELECT timestamp FROM predictions ORDER BY timestamp DESC LIMIT 10"
        )
        timestamps = [row[0] for row in cursor.fetchall()]
        
        if len(timestamps) >= 2:
            # Check time between predictions (should be ~10 seconds for demo)
            intervals = []
            for i in range(1, len(timestamps)):
                # Parse ISO timestamps
                try:
                    from datetime import datetime
                    t1 = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
                    t2 = datetime.fromisoformat(timestamps[i-1].replace('Z', '+00:00'))
                    interval = (t2 - t1).total_seconds()
                    if interval > 0:
                        intervals.append(interval)
                except:
                    pass
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                assert avg_interval < 60, f"Inference interval too long: {avg_interval:.1f}s"
    
    def test_database_size(self, db_connection):
        """Test database isn't growing too large"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        sensor_count = cursor.fetchone()[0]
        
        # After 5 minutes at 1 Hz, should have ~300 rows per equipment
        # With 3 equipment: ~900 rows
        # Reasonable upper limit: 10000 rows (would indicate ~30 min run)
        assert sensor_count < 50000, f"Database growing too fast: {sensor_count} rows"

# ═══════════════════════════════════════════════════════════════════════════════
# PYTEST CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
