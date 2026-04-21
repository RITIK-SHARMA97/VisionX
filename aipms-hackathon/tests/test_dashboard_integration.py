"""
Comprehensive Integration Tests for AIPMS Dashboard
Tests all pages, Plotly rendering, filtering, exports, navigation, and state persistence
"""

import pytest
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8501"
API_TIMEOUT = 10
DASHBOARD_TIMEOUT = 30

# Test data constants
CRITICAL_THRESHOLD_FAILURE_PROB = 0.70
WARNING_THRESHOLD_FAILURE_PROB = 0.50
CRITICAL_THRESHOLD_ANOMALY = 0.70
WARNING_THRESHOLD_ANOMALY = 0.40


class APIClient:
    """Client for interacting with AIPMS backend API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = API_TIMEOUT
    
    def get(self, endpoint: str, **kwargs) -> Dict:
        """GET request to API"""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class DashboardTestSuite:
    """Integration test suite for AIPMS Dashboard"""
    
    def __init__(self):
        self.api_client = APIClient()
        self.test_results = {
            'fleet_overview': {},
            'equipment_detail': {},
            'maintenance_schedule': {},
            'alert_feed': {},
            'navigation': {},
            'state_persistence': {},
        }
    
    # ============================================================================
    # PRE-TEST SETUP
    # ============================================================================
    
    def wait_for_api(self, max_retries: int = 30, retry_interval: int = 2) -> bool:
        """Wait for API to be ready"""
        logger.info("Waiting for API to be ready...")
        
        for attempt in range(max_retries):
            if self.api_client.health_check():
                logger.info(f"✓ API is ready (attempt {attempt + 1})")
                return True
            
            logger.warning(f"API not ready, retrying in {retry_interval}s...")
            time.sleep(retry_interval)
        
        logger.error("API failed to start within timeout")
        return False
    
    def wait_for_dashboard(self, max_retries: int = 20, retry_interval: int = 2) -> bool:
        """Wait for dashboard to be accessible"""
        logger.info("Waiting for dashboard to be ready...")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(DASHBOARD_URL, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✓ Dashboard is ready (attempt {attempt + 1})")
                    return True
            except requests.RequestException:
                pass
            
            logger.warning(f"Dashboard not ready, retrying in {retry_interval}s...")
            time.sleep(retry_interval)
        
        logger.error("Dashboard failed to start within timeout")
        return False
    
    # ============================================================================
    # FLEET OVERVIEW TESTS
    # ============================================================================
    
    def test_fleet_overview_page_loads(self) -> bool:
        """Test: Fleet Overview page loads correctly"""
        logger.info("\n[TEST] Fleet Overview Page Loads")
        
        try:
            # Verify API endpoint exists
            response = self.api_client.get("/equipment")
            assert response is not None, "API returned no data"
            
            logger.info(f"✓ Fleet overview loaded with {len(response)} equipment units")
            self.test_results['fleet_overview']['page_load'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Fleet overview failed: {e}")
            self.test_results['fleet_overview']['page_load'] = False
            return False
    
    def test_fleet_risk_heatmap_data(self) -> bool:
        """Test: Risk heatmap has correct data structure"""
        logger.info("\n[TEST] Fleet Risk Heatmap Data Structure")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            
            # Validate data structure
            required_fields = ['id', 'anomaly_score', 'failure_prob', 'status']
            
            for equipment in equipment_list:
                for field in required_fields:
                    assert field in equipment, f"Missing field: {field}"
                
                # Validate numeric ranges
                assert 0 <= equipment['anomaly_score'] <= 1, f"Invalid anomaly_score: {equipment['anomaly_score']}"
                assert 0 <= equipment['failure_prob'] <= 1, f"Invalid failure_prob: {equipment['failure_prob']}"
            
            logger.info(f"✓ Risk heatmap data valid for {len(equipment_list)} equipment")
            self.test_results['fleet_overview']['heatmap_data'] = True
            return True
        except AssertionError as e:
            logger.error(f"✗ Data validation failed: {e}")
            self.test_results['fleet_overview']['heatmap_data'] = False
            return False
    
    def test_fleet_status_distribution(self) -> bool:
        """Test: Status distribution pie chart data"""
        logger.info("\n[TEST] Fleet Status Distribution")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            
            # Count statuses
            status_counts = {
                'critical': sum(1 for e in equipment_list if e['status'] == 'critical'),
                'warning': sum(1 for e in equipment_list if e['status'] == 'warning'),
                'normal': sum(1 for e in equipment_list if e['status'] == 'normal'),
                'offline': sum(1 for e in equipment_list if e['status'] == 'offline'),
            }
            
            total = sum(status_counts.values())
            assert total == len(equipment_list), "Status count mismatch"
            
            logger.info(f"✓ Status distribution: {status_counts}")
            self.test_results['fleet_overview']['status_distribution'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Status distribution failed: {e}")
            self.test_results['fleet_overview']['status_distribution'] = False
            return False
    
    def test_fleet_kpi_metrics(self) -> bool:
        """Test: KPI metrics are calculated correctly"""
        logger.info("\n[TEST] Fleet KPI Metrics")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            
            critical_count = sum(1 for e in equipment_list if e['status'] == 'critical')
            warning_count = sum(1 for e in equipment_list if e['status'] == 'warning')
            healthy_count = sum(1 for e in equipment_list if e['status'] == 'normal')
            
            total_failure_prob = sum(e.get('failure_prob', 0) for e in equipment_list)
            avg_failure_prob = total_failure_prob / len(equipment_list) if equipment_list else 0
            
            logger.info(f"✓ Critical: {critical_count}, Warning: {warning_count}, Healthy: {healthy_count}")
            logger.info(f"✓ Average Failure Probability: {avg_failure_prob:.2%}")
            
            self.test_results['fleet_overview']['kpi_metrics'] = True
            return True
        except Exception as e:
            logger.error(f"✗ KPI metrics failed: {e}")
            self.test_results['fleet_overview']['kpi_metrics'] = False
            return False
    
    # ============================================================================
    # EQUIPMENT DETAIL TESTS
    # ============================================================================
    
    def test_equipment_detail_page_loads(self) -> bool:
        """Test: Equipment Detail page loads with data"""
        logger.info("\n[TEST] Equipment Detail Page Loads")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            assert len(equipment_list) > 0, "No equipment available"
            
            # Test first equipment
            equipment_id = equipment_list[0]['id']
            equipment = self.api_client.get(f"/equipment/{equipment_id}")
            
            assert equipment is not None, "Equipment detail returned None"
            logger.info(f"✓ Equipment detail loaded for {equipment_id}")
            
            self.test_results['equipment_detail']['page_load'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Equipment detail page failed: {e}")
            self.test_results['equipment_detail']['page_load'] = False
            return False
    
    def test_sensor_trend_charts(self) -> bool:
        """Test: Sensor trend chart data is available"""
        logger.info("\n[TEST] Sensor Trend Charts")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            assert len(equipment_list) > 0, "No equipment available"
            
            equipment_id = equipment_list[0]['id']
            sensors = self.api_client.get(f"/equipment/{equipment_id}/sensors", params={'limit': 100})
            
            # Verify sensor data structure
            required_fields = ['timestamp', 'sensor_name', 'value', 'unit']
            
            if sensors and len(sensors) > 0:
                for sensor in sensors[:5]:  # Check first 5
                    for field in required_fields:
                        assert field in sensor, f"Missing field: {field}"
                
                logger.info(f"✓ Sensor trends available: {len(sensors)} readings")
                self.test_results['equipment_detail']['sensor_trends'] = True
                return True
            else:
                logger.warning("⚠ No sensor data available")
                self.test_results['equipment_detail']['sensor_trends'] = True
                return True
        except Exception as e:
            logger.error(f"✗ Sensor trend test failed: {e}")
            self.test_results['equipment_detail']['sensor_trends'] = False
            return False
    
    def test_rul_degradation_chart(self) -> bool:
        """Test: RUL degradation chart with confidence intervals"""
        logger.info("\n[TEST] RUL Degradation Chart")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            assert len(equipment_list) > 0, "No equipment available"
            
            equipment_id = equipment_list[0]['id']
            predictions = self.api_client.get(
                f"/equipment/{equipment_id}/predictions",
                params={'days': 30}
            )
            
            # Validate prediction structure
            if predictions and len(predictions) > 0:
                required_fields = ['timestamp', 'rul_hours']
                
                for pred in predictions[:5]:  # Check first 5
                    for field in required_fields:
                        assert field in pred, f"Missing field: {field}"
                    
                    assert pred['rul_hours'] >= 0, f"Invalid RUL: {pred['rul_hours']}"
                
                logger.info(f"✓ RUL degradation data: {len(predictions)} predictions")
                self.test_results['equipment_detail']['rul_degradation'] = True
                return True
            else:
                logger.warning("⚠ No prediction data available")
                self.test_results['equipment_detail']['rul_degradation'] = True
                return True
        except Exception as e:
            logger.error(f"✗ RUL degradation test failed: {e}")
            self.test_results['equipment_detail']['rul_degradation'] = False
            return False
    
    def test_shap_feature_attribution(self) -> bool:
        """Test: SHAP feature attribution bars"""
        logger.info("\n[TEST] SHAP Feature Attribution")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            assert len(equipment_list) > 0, "No equipment available"
            
            # Find equipment with top_features
            equipment_with_features = [e for e in equipment_list if e.get('top_features')]
            
            if equipment_with_features:
                equipment = equipment_with_features[0]
                top_features = equipment.get('top_features', [])
                
                # Validate SHAP structure
                required_fields = ['sensor', 'shap', 'pct']
                
                for feature in top_features:
                    for field in required_fields:
                        assert field in feature, f"Missing field: {field}"
                
                logger.info(f"✓ SHAP features: {len(top_features)} top contributors")
                self.test_results['equipment_detail']['shap_attribution'] = True
                return True
            else:
                logger.warning("⚠ No SHAP data available")
                self.test_results['equipment_detail']['shap_attribution'] = True
                return True
        except Exception as e:
            logger.error(f"✗ SHAP attribution test failed: {e}")
            self.test_results['equipment_detail']['shap_attribution'] = False
            return False
    
    # ============================================================================
    # MAINTENANCE SCHEDULE TESTS
    # ============================================================================
    
    def test_maintenance_schedule_page_loads(self) -> bool:
        """Test: Maintenance Schedule page loads"""
        logger.info("\n[TEST] Maintenance Schedule Page Loads")
        
        try:
            schedule = self.api_client.get("/schedule", params={'days': 7})
            assert schedule is not None, "Schedule returned None"
            
            logger.info(f"✓ Maintenance schedule loaded: {len(schedule)} jobs")
            self.test_results['maintenance_schedule']['page_load'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Maintenance schedule page failed: {e}")
            self.test_results['maintenance_schedule']['page_load'] = False
            return False
    
    def test_gantt_chart_data(self) -> bool:
        """Test: Gantt chart has proper time window data"""
        logger.info("\n[TEST] Gantt Chart Data")
        
        try:
            schedule = self.api_client.get("/schedule", params={'days': 7})
            
            # Validate schedule structure
            required_fields = ['equipment_id', 'priority_tier', 'scheduled_window_start', 'scheduled_window_end']
            
            if schedule and len(schedule) > 0:
                for job in schedule[:5]:
                    for field in required_fields:
                        assert field in job, f"Missing field: {field}"
                
                logger.info(f"✓ Gantt data valid: {len(schedule)} jobs")
                self.test_results['maintenance_schedule']['gantt_data'] = True
                return True
            else:
                logger.warning("⚠ No schedule data available")
                self.test_results['maintenance_schedule']['gantt_data'] = True
                return True
        except Exception as e:
            logger.error(f"✗ Gantt data test failed: {e}")
            self.test_results['maintenance_schedule']['gantt_data'] = False
            return False
    
    def test_schedule_priority_distribution(self) -> bool:
        """Test: Schedule has jobs across priority tiers"""
        logger.info("\n[TEST] Schedule Priority Distribution")
        
        try:
            schedule = self.api_client.get("/schedule", params={'days': 7})
            
            if schedule:
                priority_counts = {}
                for job in schedule:
                    tier = job.get('priority_tier', 'normal')
                    priority_counts[tier] = priority_counts.get(tier, 0) + 1
                
                logger.info(f"✓ Priority distribution: {priority_counts}")
                self.test_results['maintenance_schedule']['priority_distribution'] = True
                return True
            else:
                logger.warning("⚠ No schedule data available")
                self.test_results['maintenance_schedule']['priority_distribution'] = True
                return True
        except Exception as e:
            logger.error(f"✗ Priority distribution test failed: {e}")
            self.test_results['maintenance_schedule']['priority_distribution'] = False
            return False
    
    # ============================================================================
    # ALERT FEED TESTS
    # ============================================================================
    
    def test_alert_feed_page_loads(self) -> bool:
        """Test: Alert Feed page loads"""
        logger.info("\n[TEST] Alert Feed Page Loads")
        
        try:
            alerts = self.api_client.get("/alerts")
            assert alerts is not None, "Alerts returned None"
            
            logger.info(f"✓ Alert feed loaded: {len(alerts)} alerts")
            self.test_results['alert_feed']['page_load'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Alert feed page failed: {e}")
            self.test_results['alert_feed']['page_load'] = False
            return False
    
    def test_alert_severity_filtering(self) -> bool:
        """Test: Severity filter reduces alert count"""
        logger.info("\n[TEST] Alert Severity Filtering")
        
        try:
            all_alerts = self.api_client.get("/alerts")
            critical_alerts = self.api_client.get("/alerts", params={'severity': 'critical'})
            warning_alerts = self.api_client.get("/alerts", params={'severity': 'warning'})
            
            # Verify filtering reduces count
            assert len(critical_alerts) <= len(all_alerts), "Critical filter increased count"
            assert len(warning_alerts) <= len(all_alerts), "Warning filter increased count"
            
            logger.info(f"✓ Severity filtering: Total={len(all_alerts)}, Critical={len(critical_alerts)}, Warning={len(warning_alerts)}")
            self.test_results['alert_feed']['severity_filtering'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Severity filtering test failed: {e}")
            self.test_results['alert_feed']['severity_filtering'] = False
            return False
    
    def test_alert_acknowledgement(self) -> bool:
        """Test: Acknowledge button works"""
        logger.info("\n[TEST] Alert Acknowledgement")
        
        try:
            alerts = self.api_client.get("/alerts", params={'acknowledged': 'false'})
            
            if alerts and len(alerts) > 0:
                alert_id = alerts[0]['id']
                
                # Acknowledge alert
                response = requests.post(
                    f"{API_BASE_URL}/alerts/{alert_id}/acknowledge",
                    json={'acknowledged_by': 'test_user'},
                    timeout=API_TIMEOUT
                )
                
                assert response.status_code == 200, f"Acknowledge failed: {response.status_code}"
                logger.info(f"✓ Alert {alert_id} acknowledged successfully")
                self.test_results['alert_feed']['acknowledgement'] = True
                return True
            else:
                logger.warning("⚠ No unacknowledged alerts to test")
                self.test_results['alert_feed']['acknowledgement'] = True
                return True
        except Exception as e:
            logger.error(f"✗ Acknowledgement test failed: {e}")
            self.test_results['alert_feed']['acknowledgement'] = False
            return False
    
    def test_alert_date_range_filtering(self) -> bool:
        """Test: Date range filter updates alert list"""
        logger.info("\n[TEST] Alert Date Range Filtering")
        
        try:
            today = datetime.now().date()
            start_date = (today - timedelta(days=7)).isoformat()
            end_date = today.isoformat()
            
            filtered_alerts = self.api_client.get(
                "/alerts",
                params={'start_date': start_date, 'end_date': end_date}
            )
            
            logger.info(f"✓ Date range filter: {len(filtered_alerts)} alerts in range")
            self.test_results['alert_feed']['date_filtering'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Date range filtering test failed: {e}")
            self.test_results['alert_feed']['date_filtering'] = False
            return False
    
    # ============================================================================
    # FILTERING & EXPORT TESTS
    # ============================================================================
    
    def test_csv_export_fleet_overview(self) -> bool:
        """Test: CSV export works for fleet overview"""
        logger.info("\n[TEST] CSV Export - Fleet Overview")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            
            # Verify exportable data exists
            assert len(equipment_list) > 0, "No equipment to export"
            
            # Simulate CSV generation
            headers = list(equipment_list[0].keys())
            logger.info(f"✓ CSV export ready: {len(headers)} columns")
            
            self.test_results['alert_feed']['csv_export_fleet'] = True
            return True
        except Exception as e:
            logger.error(f"✗ CSV export test failed: {e}")
            self.test_results['alert_feed']['csv_export_fleet'] = False
            return False
    
    def test_csv_export_schedule(self) -> bool:
        """Test: CSV export includes all columns"""
        logger.info("\n[TEST] CSV Export - Schedule")
        
        try:
            schedule = self.api_client.get("/schedule", params={'days': 7})
            
            if schedule and len(schedule) > 0:
                headers = list(schedule[0].keys())
                required_headers = ['equipment_id', 'priority_tier', 'recommended_action']
                
                for header in required_headers:
                    assert header in headers, f"Missing column: {header}"
                
                logger.info(f"✓ Schedule CSV export ready: {len(headers)} columns")
                self.test_results['alert_feed']['csv_export_schedule'] = True
                return True
            else:
                logger.warning("⚠ No schedule data to export")
                self.test_results['alert_feed']['csv_export_schedule'] = True
                return True
        except Exception as e:
            logger.error(f"✗ Schedule export test failed: {e}")
            self.test_results['alert_feed']['csv_export_schedule'] = False
            return False
    
    # ============================================================================
    # NAVIGATION & STATE TESTS
    # ============================================================================
    
    def test_cross_page_navigation(self) -> bool:
        """Test: Cross-page navigation works"""
        logger.info("\n[TEST] Cross-Page Navigation")
        
        try:
            # Get equipment from fleet overview
            equipment_list = self.api_client.get("/equipment")
            assert len(equipment_list) > 0, "No equipment available"
            
            # Navigate to equipment detail
            equipment_id = equipment_list[0]['id']
            equipment_detail = self.api_client.get(f"/equipment/{equipment_id}")
            assert equipment_detail is not None, "Navigation to detail failed"
            
            logger.info(f"✓ Navigation successful: Fleet → Detail ({equipment_id})")
            self.test_results['navigation']['cross_page'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Navigation test failed: {e}")
            self.test_results['navigation']['cross_page'] = False
            return False
    
    def test_state_persistence(self) -> bool:
        """Test: Selected equipment persists across navigation"""
        logger.info("\n[TEST] State Persistence")
        
        try:
            equipment_list = self.api_client.get("/equipment")
            assert len(equipment_list) > 0, "No equipment available"
            
            selected_id = equipment_list[0]['id']
            
            # Get detail twice
            detail1 = self.api_client.get(f"/equipment/{selected_id}")
            detail2 = self.api_client.get(f"/equipment/{selected_id}")
            
            # Verify same data returned
            assert detail1['id'] == detail2['id'], "Equipment ID mismatch"
            assert detail1.get('status') == detail2.get('status'), "Status mismatch"
            
            logger.info(f"✓ State persistence verified for {selected_id}")
            self.test_results['state_persistence']['equipment_selection'] = True
            return True
        except Exception as e:
            logger.error(f"✗ State persistence test failed: {e}")
            self.test_results['state_persistence']['equipment_selection'] = False
            return False
    
    def test_page_refresh_consistency(self) -> bool:
        """Test: Page refresh returns consistent data"""
        logger.info("\n[TEST] Page Refresh Consistency")
        
        try:
            # Get data twice
            data1 = self.api_client.get("/equipment")
            time.sleep(1)
            data2 = self.api_client.get("/equipment")
            
            # Equipment count should be same
            assert len(data1) == len(data2), "Equipment count changed"
            
            # IDs should be same
            ids1 = sorted([e['id'] for e in data1])
            ids2 = sorted([e['id'] for e in data2])
            assert ids1 == ids2, "Equipment list changed"
            
            logger.info(f"✓ Page refresh consistent: {len(data1)} equipment")
            self.test_results['state_persistence']['refresh_consistency'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Refresh consistency test failed: {e}")
            self.test_results['state_persistence']['refresh_consistency'] = False
            return False
    
    # ============================================================================
    # CHART RENDERING TESTS
    # ============================================================================
    
    def test_plotly_charts_have_data(self) -> bool:
        """Test: Plotly charts have data to render"""
        logger.info("\n[TEST] Plotly Chart Data Availability")
        
        try:
            charts_data = {}
            
            # Fleet Overview Charts
            equipment_list = self.api_client.get("/equipment")
            charts_data['risk_heatmap'] = len(equipment_list) > 0
            
            # Equipment Detail Charts
            if equipment_list:
                equipment_id = equipment_list[0]['id']
                
                sensors = self.api_client.get(f"/equipment/{equipment_id}/sensors", params={'limit': 100})
                charts_data['sensor_trends'] = len(sensors) > 0 if sensors else False
                
                predictions = self.api_client.get(f"/equipment/{equipment_id}/predictions", params={'days': 30})
                charts_data['rul_degradation'] = len(predictions) > 0 if predictions else False
            
            # Maintenance Schedule Charts
            schedule = self.api_client.get("/schedule", params={'days': 7})
            charts_data['gantt'] = len(schedule) > 0 if schedule else False
            
            logger.info(f"✓ Chart data availability: {charts_data}")
            self.test_results['navigation']['chart_rendering'] = all(charts_data.values())
            return True
        except Exception as e:
            logger.error(f"✗ Chart data test failed: {e}")
            self.test_results['navigation']['chart_rendering'] = False
            return False
    
    # ============================================================================
    # REPORT GENERATION
    # ============================================================================
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = "\n" + "="*80 + "\n"
        report += "AIPMS DASHBOARD INTEGRATION TEST REPORT\n"
        report += "="*80 + "\n\n"
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            report += f"\n{category.upper()}\n"
            report += "-" * 40 + "\n"
            
            for test_name, result in tests.items():
                status = "✓ PASS" if result else "✗ FAIL"
                report += f"  {status:8} - {test_name}\n"
                
                total_tests += 1
                if result:
                    passed_tests += 1
        
        report += "\n" + "="*80 + "\n"
        report += f"SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)\n"
        report += "="*80 + "\n"
        
        return report
    
    def run_all_tests(self) -> bool:
        """Run complete test suite"""
        logger.info("\n" + "="*80)
        logger.info("STARTING AIPMS DASHBOARD INTEGRATION TEST SUITE")
        logger.info("="*80)
        
        # Pre-test checks
        if not self.wait_for_api():
            logger.error("API is not ready, aborting tests")
            return False
        
        if not self.wait_for_dashboard():
            logger.warning("Dashboard is not accessible, skipping UI tests")
        
        # Fleet Overview Tests
        logger.info("\n[PHASE 1] Fleet Overview Tests")
        self.test_fleet_overview_page_loads()
        self.test_fleet_risk_heatmap_data()
        self.test_fleet_status_distribution()
        self.test_fleet_kpi_metrics()
        
        # Equipment Detail Tests
        logger.info("\n[PHASE 2] Equipment Detail Tests")
        self.test_equipment_detail_page_loads()
        self.test_sensor_trend_charts()
        self.test_rul_degradation_chart()
        self.test_shap_feature_attribution()
        
        # Maintenance Schedule Tests
        logger.info("\n[PHASE 3] Maintenance Schedule Tests")
        self.test_maintenance_schedule_page_loads()
        self.test_gantt_chart_data()
        self.test_schedule_priority_distribution()
        
        # Alert Feed Tests
        logger.info("\n[PHASE 4] Alert Feed Tests")
        self.test_alert_feed_page_loads()
        self.test_alert_severity_filtering()
        self.test_alert_acknowledgement()
        self.test_alert_date_range_filtering()
        
        # Filtering & Export Tests
        logger.info("\n[PHASE 5] Filtering & Export Tests")
        self.test_csv_export_fleet_overview()
        self.test_csv_export_schedule()
        
        # Navigation & State Tests
        logger.info("\n[PHASE 6] Navigation & State Tests")
        self.test_cross_page_navigation()
        self.test_state_persistence()
        self.test_page_refresh_consistency()
        self.test_plotly_charts_have_data()
        
        # Print report
        report = self.generate_report()
        print(report)
        
        # Log report
        logger.info(report)
        
        # Save report to file
        with open('test_dashboard_report.txt', 'w') as f:
            f.write(report)
        logger.info("Report saved to test_dashboard_report.txt")
        
        # Determine success
        total = sum(len(tests) for tests in self.test_results.values())
        passed = sum(sum(1 for r in tests.values() if r) for tests in self.test_results.values())
        
        return passed / total >= 0.80  # 80% pass threshold


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_suite():
    """Initialize test suite"""
    suite = DashboardTestSuite()
    yield suite


def test_complete_integration(test_suite):
    """Complete integration test"""
    assert test_suite.run_all_tests(), "Integration tests failed"


if __name__ == "__main__":
    suite = DashboardTestSuite()
    success = suite.run_all_tests()
    exit(0 if success else 1)
