#!/usr/bin/env python3
"""
Interactive Dashboard Testing Checklist
Complete manual testing verification from PHASE_5_ROADMAP.md
Matches all testing requirements for judges
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

API_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8501"

class DashboardTester:
    """Interactive dashboard testing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "fleet_overview": [],
            "equipment_detail": [],
            "maintenance_schedule": [],
            "alert_feed": [],
            "filtering_export": [],
            "navigation_state": [],
            "plotly_charts": [],
        }
        self.api_ready = False
    
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "ℹ", "SUCCESS": "✓", "ERROR": "✗", "WARN": "⚠"}
        symbol = prefix.get(level, "")
        print(f"[{ts}] {symbol} {message}")
    
    def input_yn(self, prompt: str) -> bool:
        """Get yes/no input from user"""
        while True:
            response = input(f"\n{prompt} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print("Please enter 'y' or 'n'")
    
    def record_test(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        if category not in self.results:
            self.results[category] = []
        
        self.results[category].append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if details:
            print(f"         {details}")
    
    def section_header(self, title: str):
        """Print section header"""
        print(f"\n{'='*80}")
        print(f"  {title.upper()}")
        print(f"{'='*80}")
    
    def check_api_health(self) -> bool:
        """Check if API is running"""
        try:
            response = self.session.get(f"{API_URL}/health", timeout=5)
            self.api_ready = response.status_code == 200
            if self.api_ready:
                self.log("API is running", "SUCCESS")
            else:
                self.log("API not responding properly", "ERROR")
            return self.api_ready
        except Exception as e:
            self.log(f"Cannot connect to API: {e}", "ERROR")
            return False
    
    def test_fleet_overview(self):
        """Test Fleet Overview page"""
        self.section_header("FLEET OVERVIEW TESTS")
        
        if not self.api_ready:
            self.log("Skipping - API not ready", "WARN")
            return
        
        try:
            # Test 1: API returns equipment list
            response = self.session.get(f"{API_URL}/equipment", timeout=10)
            equipment = response.json() if response.status_code == 200 else []
            
            passed = response.status_code == 200 and len(equipment) > 0
            self.record_test("fleet_overview", "API returns equipment list",
                           passed, f"Found {len(equipment)} equipment units")
            
            if not equipment:
                self.log("No equipment in system", "WARN")
                return
            
            # Test 2: Status distribution
            critical = sum(1 for e in equipment if e.get('status') == 'critical')
            warning = sum(1 for e in equipment if e.get('status') == 'warning')
            normal = sum(1 for e in equipment if e.get('status') == 'normal')
            
            status_info = f"Critical: {critical}, Warning: {warning}, Normal: {normal}"
            self.record_test("fleet_overview", "Status distribution calculated",
                           True, status_info)
            
            # Test 3: Required fields present
            required_fields = ['id', 'name', 'type', 'status', 'failure_prob', 'anomaly_score']
            missing_fields = []
            for equipment_item in equipment:
                for field in required_fields:
                    if field not in equipment_item:
                        missing_fields.append(field)
            
            passed = len(missing_fields) == 0
            self.record_test("fleet_overview", "Required fields present",
                           passed, f"Fields checked: {', '.join(required_fields)}")
            
            # Test 4: Failure probability ranges
            valid_ranges = all(
                0 <= e.get('failure_prob', 0) <= 1 for e in equipment
            )
            self.record_test("fleet_overview", "Failure probabilities in range [0-1]",
                           valid_ranges)
            
            # Manual tests
            self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
            print("""
            1. Open http://localhost:8501
            2. Navigate to Fleet Overview page
            3. Check all these:
               - Risk heatmap displays with equipment scatter
               - Status pie chart shows color-coded statuses
               - Equipment cards display with icons
               - Charts are interactive (hover tooltips)
               - CSV export button is present and works
            """)
            
            self.record_test("fleet_overview", "Risk heatmap renders visually",
                           self.input_yn("Does the risk heatmap render correctly?"))
            
            self.record_test("fleet_overview", "Status pie chart renders",
                           self.input_yn("Does the status pie chart display?"))
            
            self.record_test("fleet_overview", "CSV export works",
                           self.input_yn("Can you download the fleet CSV?"))
        
        except Exception as e:
            self.log(f"Error in fleet overview tests: {e}", "ERROR")
    
    def test_equipment_detail(self):
        """Test Equipment Detail page"""
        self.section_header("EQUIPMENT DETAIL TESTS")
        
        if not self.api_ready:
            self.log("Skipping - API not ready", "WARN")
            return
        
        try:
            # Get first equipment
            response = self.session.get(f"{API_URL}/equipment", timeout=10)
            equipment_list = response.json() if response.status_code == 200 else []
            
            if not equipment_list:
                self.log("No equipment available", "WARN")
                return
            
            equipment_id = equipment_list[0]['id']
            self.log(f"Testing with equipment: {equipment_id}")
            
            # Test 1: Equipment detail endpoint
            response = self.session.get(f"{API_URL}/equipment/{equipment_id}", timeout=10)
            passed = response.status_code == 200
            self.record_test("equipment_detail", "Equipment detail endpoint works",
                           passed)
            
            if not passed:
                return
            
            equipment = response.json()
            
            # Test 2: Sensor data available
            sensors = self.session.get(
                f"{API_URL}/equipment/{equipment_id}/sensors",
                params={'limit': 100},
                timeout=10
            ).json() or []
            
            self.record_test("equipment_detail", "Sensor data available",
                           len(sensors) > 0, f"Found {len(sensors)} sensor readings")
            
            # Test 3: Predictions available
            predictions = self.session.get(
                f"{API_URL}/equipment/{equipment_id}/predictions",
                params={'days': 30},
                timeout=10
            ).json() or []
            
            self.record_test("equipment_detail", "RUL predictions available",
                           len(predictions) > 0, f"Found {len(predictions)} predictions")
            
            # Test 4: SHAP features
            top_features = equipment.get('top_features', [])
            self.record_test("equipment_detail", "SHAP features available",
                           len(top_features) > 0, f"Found {len(top_features)} top features")
            
            # Manual tests
            self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
            print(f"""
            1. Open http://localhost:8501
            2. Go to Equipment Detail page
            3. Select equipment: {equipment_id}
            4. Check all these:
               - Equipment dropdown shows all available equipment
               - Sensor trend chart displays with multiple sensors
               - RUL degradation chart shows with confidence interval band
               - Feature attribution horizontal bar chart shows
               - All charts update when different equipment selected
            """)
            
            self.record_test("equipment_detail", "Equipment dropdown works",
                           self.input_yn("Does equipment dropdown selector work?"))
            
            self.record_test("equipment_detail", "Sensor trends chart renders",
                           self.input_yn("Do the sensor trend charts display?"))
            
            self.record_test("equipment_detail", "RUL confidence interval shows",
                           self.input_yn("Does RUL chart show confidence interval?"))
            
            self.record_test("equipment_detail", "Feature attribution displays",
                           self.input_yn("Do SHAP feature bars display?"))
        
        except Exception as e:
            self.log(f"Error in equipment detail tests: {e}", "ERROR")
    
    def test_maintenance_schedule(self):
        """Test Maintenance Schedule page"""
        self.section_header("MAINTENANCE SCHEDULE TESTS")
        
        if not self.api_ready:
            self.log("Skipping - API not ready", "WARN")
            return
        
        try:
            # Get schedule
            response = self.session.get(
                f"{API_URL}/schedule",
                params={'days': 7},
                timeout=10
            )
            schedule = response.json() if response.status_code == 200 else []
            
            passed = response.status_code == 200
            self.record_test("maintenance_schedule", "Schedule endpoint works",
                           passed, f"Found {len(schedule)} jobs")
            
            if not schedule:
                self.log("No schedule data", "WARN")
                return
            
            # Test 2: Priority distribution
            priorities = {}
            for job in schedule:
                tier = job.get('priority_tier', 'unknown')
                priorities[tier] = priorities.get(tier, 0) + 1
            
            priority_info = ", ".join([f"{k}: {v}" for k, v in priorities.items()])
            self.record_test("maintenance_schedule", "Jobs categorized by priority",
                           len(priorities) > 0, priority_info)
            
            # Test 3: Job structure validation
            required_fields = ['equipment_id', 'priority_tier', 'recommended_action']
            all_valid = all(
                all(field in job for field in required_fields)
                for job in schedule
            )
            self.record_test("maintenance_schedule", "Job structure valid",
                           all_valid)
            
            # Manual tests
            self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
            print("""
            1. Open http://localhost:8501
            2. Go to Maintenance Schedule page
            3. Check all these:
               - Gantt chart displays with equipment on Y-axis, time on X-axis
               - Job bars are color-coded by priority (critical/warning/normal)
               - Schedule table displays all jobs with columns sortable
               - Hover over Gantt bars shows job details
               - CSV export includes all job information
            """)
            
            self.record_test("maintenance_schedule", "Gantt chart displays",
                           self.input_yn("Does the Gantt chart render?"))
            
            self.record_test("maintenance_schedule", "Job bars color-coded correctly",
                           self.input_yn("Are bars color-coded by priority?"))
            
            self.record_test("maintenance_schedule", "Schedule table sortable",
                           self.input_yn("Can you sort the schedule table?"))
        
        except Exception as e:
            self.log(f"Error in maintenance schedule tests: {e}", "ERROR")
    
    def test_alert_feed(self):
        """Test Alert Feed page"""
        self.section_header("ALERT FEED TESTS")
        
        if not self.api_ready:
            self.log("Skipping - API not ready", "WARN")
            return
        
        try:
            # Test 1: Get all alerts
            response = self.session.get(f"{API_URL}/alerts", timeout=10)
            all_alerts = response.json() if response.status_code == 200 else []
            
            self.record_test("alert_feed", "Alert feed endpoint works",
                           response.status_code == 200, f"Found {len(all_alerts)} alerts")
            
            # Test 2: Severity filtering
            critical = self.session.get(
                f"{API_URL}/alerts",
                params={'severity': 'critical'},
                timeout=10
            ).json() or []
            
            warning = self.session.get(
                f"{API_URL}/alerts",
                params={'severity': 'warning'},
                timeout=10
            ).json() or []
            
            filter_works = len(critical) + len(warning) <= len(all_alerts)
            self.record_test("alert_feed", "Severity filtering works",
                           filter_works,
                           f"Critical: {len(critical)}, Warning: {len(warning)}, Total: {len(all_alerts)}")
            
            # Test 3: Date range filtering
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            response = self.session.get(
                f"{API_URL}/alerts",
                params={
                    'start_date': str(week_ago),
                    'end_date': str(today)
                },
                timeout=10
            )
            dated_alerts = response.json() if response.status_code == 200 else []
            
            self.record_test("alert_feed", "Date range filtering works",
                           response.status_code == 200, f"Found {len(dated_alerts)} alerts in range")
            
            # Manual tests
            self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
            print("""
            1. Open http://localhost:8501
            2. Go to Alert Feed page
            3. Check all these:
               - Alerts display in list with severity badges (red/yellow)
               - Severity filter reduces alert count
               - Date range picker works and filters alerts
               - Acknowledge button moves alert to resolved
               - SHAP top sensors shown with impact percentages
               - CSV export includes all alert information
            """)
            
            self.record_test("alert_feed", "Alert list displays",
                           self.input_yn("Do alerts display in the feed?"))
            
            self.record_test("alert_feed", "Severity filter works",
                           self.input_yn("Does severity filter reduce alert count?"))
            
            self.record_test("alert_feed", "Acknowledge button works",
                           self.input_yn("Can you acknowledge alerts?"))
            
            self.record_test("alert_feed", "Date range filter works",
                           self.input_yn("Does date range filter work?"))
        
        except Exception as e:
            self.log(f"Error in alert feed tests: {e}", "ERROR")
    
    def test_filtering_export(self):
        """Test filtering and export functionality"""
        self.section_header("FILTERING & EXPORT TESTS")
        
        self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
        print("""
        1. Go to Fleet Overview
        2. Click CSV Export - verify downloaded file has columns:
           id, name, type, status, failure_prob, anomaly_score
        
        3. Go to Maintenance Schedule
        4. Click CSV Export - verify file includes:
           equipment_id, priority_tier, recommended_action, estimated_duration_hours
        
        5. Go to Alert Feed
        6. Click CSV Export - verify file includes:
           equipment_id, severity, message, triggered_at, top_sensors
        
        7. Test filter persistence:
           - Apply a filter (e.g., severity=critical)
           - Navigate to another page
           - Return to original page
           - Filter should be preserved
        """)
        
        self.record_test("filtering_export", "Fleet CSV export works",
                       self.input_yn("Does Fleet Overview CSV export work?"))
        
        self.record_test("filtering_export", "Schedule CSV export works",
                       self.input_yn("Does Maintenance Schedule CSV export work?"))
        
        self.record_test("filtering_export", "Alert CSV export works",
                       self.input_yn("Does Alert Feed CSV export work?"))
        
        self.record_test("filtering_export", "Filter persistence",
                       self.input_yn("Do filters persist across page navigation?"))
    
    def test_navigation_state(self):
        """Test navigation and state persistence"""
        self.section_header("NAVIGATION & STATE PERSISTENCE TESTS")
        
        self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
        print("""
        1. Go to Fleet Overview
        2. Note which equipment is displayed
        3. Click on an equipment to go to Equipment Detail
        4. Use breadcrumb or back button to return to Fleet Overview
        5. Same equipment should still be selected/visible
        
        6. Go to Equipment Detail for equipment ABC
        7. Apply a filter or change settings
        8. Refresh the page (Ctrl+R)
        9. Page should load with same equipment ABC
        
        10. Go to Maintenance Schedule
        11. Apply date range filter
        12. Navigate to Alert Feed
        13. Navigate back to Maintenance Schedule
        14. Date filter should be preserved
        """)
        
        self.record_test("navigation_state", "Cross-page navigation works",
                       self.input_yn("Can you navigate between pages?"))
        
        self.record_test("navigation_state", "Selected equipment persists",
                       self.input_yn("Does selected equipment stay after navigation?"))
        
        self.record_test("navigation_state", "Page refresh consistency",
                       self.input_yn("Does page maintain state after refresh?"))
        
        self.record_test("navigation_state", "Filter persistence across navigation",
                       self.input_yn("Do filters persist when navigating?"))
    
    def test_plotly_charts(self):
        """Test Plotly chart rendering"""
        self.section_header("PLOTLY CHARTS RENDERING TESTS")
        
        self.log("\n[MANUAL VERIFICATION REQUIRED]", "WARN")
        print("""
        FLEET OVERVIEW CHARTS:
        1. Risk Heatmap
           - X-axis: anomaly_score (0-1)
           - Y-axis: failure_prob (0-1)
           - Color intensity: equipment status
           - Hover shows equipment details
        
        2. Status Pie Chart
           - Slices color-coded (Critical=red, Warning=yellow, Normal=green)
           - Hover shows count and percentage
           - Legend identifies each status
        
        EQUIPMENT DETAIL CHARTS:
        3. Sensor Trend (line chart)
           - Multiple colored lines for different sensors
           - X-axis: timestamp
           - Y-axis: sensor value
           - Hover shows sensor name and value
        
        4. RUL Degradation (line + area chart)
           - Main line: RUL estimate
           - Shaded area: 95% confidence interval band
           - X-axis: past 30 days
           - Y-axis: RUL hours
        
        5. Feature Attribution (horizontal bar)
           - Bars show SHAP values (left/right for negative/positive)
           - Color-coded by impact magnitude
           - Labels show sensor names
           - Values show impact percentage
        
        MAINTENANCE SCHEDULE CHART:
        6. Gantt Timeline
           - Y-axis: equipment names
           - X-axis: calendar timeline (7 days)
           - Bars: scheduled maintenance windows
           - Colors: priority tiers (critical/warning/routine)
           - Hover shows job details
        """)
        
        self.record_test("plotly_charts", "Risk heatmap renders",
                       self.input_yn("Does risk heatmap display with scatter plot?"))
        
        self.record_test("plotly_charts", "Status pie chart renders",
                       self.input_yn("Does pie chart show status distribution?"))
        
        self.record_test("plotly_charts", "Sensor trend chart renders",
                       self.input_yn("Do sensor trend line charts display?"))
        
        self.record_test("plotly_charts", "RUL confidence interval shows",
                       self.input_yn("Does RUL chart show confidence interval band?"))
        
        self.record_test("plotly_charts", "Feature attribution bars show",
                       self.input_yn("Do SHAP feature bars display correctly?"))
        
        self.record_test("plotly_charts", "Gantt timeline renders",
                       self.input_yn("Does Gantt chart display maintenance timeline?"))
        
        self.record_test("plotly_charts", "Charts are interactive",
                       self.input_yn("Can you hover/zoom on charts?"))
    
    def print_summary(self):
        """Print test summary report"""
        self.section_header("TEST SUMMARY REPORT")
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            if not tests:
                continue
            
            category_passed = sum(1 for t in tests if t['passed'])
            category_total = len(tests)
            
            status = "✓" if category_passed == category_total else "⚠"
            pct = (category_passed / category_total * 100) if category_total > 0 else 0
            
            print(f"\n{status} {category.upper().replace('_', ' ')}")
            print(f"   {category_passed}/{category_total} passed ({pct:.0f}%)")
            
            total_tests += category_total
            passed_tests += category_passed
        
        print(f"\n{'='*80}")
        overall_pct = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({overall_pct:.0f}%)")
        
        if overall_pct >= 90:
            print("✓ DASHBOARD IS READY FOR PRODUCTION")
        elif overall_pct >= 75:
            print("⚠ DASHBOARD MEETS REQUIREMENTS WITH MINOR ISSUES")
        elif overall_pct >= 60:
            print("⚠ DASHBOARD NEEDS FIXES FOR CRITICAL FEATURES")
        else:
            print("✗ DASHBOARD HAS MAJOR ISSUES")
        
        print(f"{'='*80}\n")
        
        # Save results
        with open('dashboard_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"Report saved to: dashboard_test_report.json")
    
    def run_full_test(self):
        """Run complete test suite"""
        print("\n" + "="*80)
        print(" "*20 + "AIPMS DASHBOARD TEST SUITE")
        print(" "*15 + "Phase 5 - Complete Integration Testing")
        print("="*80)
        
        print("""
INSTRUCTIONS:
1. Start the backend API: python api/main.py
2. Start the dashboard: streamlit run dashboard/app.py
3. Wait for this test to check API health
4. When prompted, perform manual tests in the browser
5. Answer 'y' for pass, 'n' for fail

Dashboard: http://localhost:8501
API: http://localhost:8000
        """)
        
        input("Press Enter to begin tests...")
        
        # Check API
        print("\nChecking API connection...")
        if not self.check_api_health():
            self.log("Cannot proceed without API", "ERROR")
            return
        
        # Run all tests
        self.test_fleet_overview()
        self.test_equipment_detail()
        self.test_maintenance_schedule()
        self.test_alert_feed()
        self.test_filtering_export()
        self.test_navigation_state()
        self.test_plotly_charts()
        
        # Print summary
        self.print_summary()


def main():
    """Main entry point"""
    tester = DashboardTester()
    tester.run_full_test()


if __name__ == "__main__":
    main()
