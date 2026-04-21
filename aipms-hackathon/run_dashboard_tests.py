"""
Complete Test Runner for AIPMS Dashboard
Starts API, Dashboard, and runs integration tests
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_DIR = Path(__file__).parent.parent
API_PORT = 8000
DASHBOARD_PORT = 8501
STARTUP_TIMEOUT = 30  # seconds

class TestRunner:
    def __init__(self):
        self.api_process = None
        self.dashboard_process = None
        self.test_start_time = None
        self.test_results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level:8}] {message}")
    
    def start_api(self) -> bool:
        """Start FastAPI backend"""
        self.log("Starting FastAPI backend...")
        
        try:
            # Change to project directory
            api_script = PROJECT_DIR / "api" / "main.py"
            
            self.api_process = subprocess.Popen(
                [sys.executable, str(api_script)],
                cwd=str(PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log(f"API process started (PID: {self.api_process.pid})")
            
            # Wait for API to be ready
            import requests
            start_time = time.time()
            
            while time.time() - start_time < STARTUP_TIMEOUT:
                try:
                    response = requests.get(f"http://localhost:{API_PORT}/health", timeout=2)
                    if response.status_code == 200:
                        self.log("✓ API is ready", "SUCCESS")
                        return True
                except requests.RequestException:
                    time.sleep(2)
            
            self.log("✗ API failed to start within timeout", "ERROR")
            return False
        except Exception as e:
            self.log(f"✗ Failed to start API: {e}", "ERROR")
            return False
    
    def start_dashboard(self) -> bool:
        """Start Streamlit dashboard"""
        self.log("Starting Streamlit dashboard...")
        
        try:
            dashboard_script = PROJECT_DIR / "dashboard" / "app.py"
            
            self.dashboard_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", str(dashboard_script),
                 "--server.port", str(DASHBOARD_PORT),
                 "--logger.level", "warning"],
                cwd=str(PROJECT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log(f"Dashboard process started (PID: {self.dashboard_process.pid})")
            
            # Wait for dashboard to be ready
            import requests
            start_time = time.time()
            
            while time.time() - start_time < STARTUP_TIMEOUT:
                try:
                    response = requests.get(f"http://localhost:{DASHBOARD_PORT}", timeout=2)
                    if response.status_code == 200:
                        self.log("✓ Dashboard is ready", "SUCCESS")
                        return True
                except requests.RequestException:
                    time.sleep(2)
            
            self.log("⚠ Dashboard may not be fully ready (will continue anyway)", "WARNING")
            return True
        except Exception as e:
            self.log(f"✗ Failed to start dashboard: {e}", "ERROR")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run integration test suite"""
        self.log("Running integration tests...")
        self.test_start_time = time.time()
        
        try:
            test_file = PROJECT_DIR / "tests" / "test_dashboard_integration.py"
            
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(PROJECT_DIR),
                capture_output=False,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            elapsed = time.time() - self.test_start_time
            
            if result.returncode == 0:
                self.log(f"✓ Integration tests passed ({elapsed:.1f}s)", "SUCCESS")
                return True
            else:
                self.log(f"✗ Integration tests failed ({elapsed:.1f}s)", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            self.log("✗ Integration tests timed out after 5 minutes", "ERROR")
            return False
        except Exception as e:
            self.log(f"✗ Failed to run tests: {e}", "ERROR")
            return False
    
    def run_pytest(self) -> bool:
        """Run pytest on integration tests"""
        self.log("Running pytest suite...")
        
        try:
            test_file = PROJECT_DIR / "tests" / "test_dashboard_integration.py"
            
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                cwd=str(PROJECT_DIR),
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✓ Pytest suite passed", "SUCCESS")
                return True
            else:
                self.log("✗ Pytest suite failed", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            self.log("✗ Pytest timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"✗ Failed to run pytest: {e}", "ERROR")
            return False
    
    def stop_services(self):
        """Stop API and Dashboard"""
        self.log("Shutting down services...")
        
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                self.log(f"API process stopped", "INFO")
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                self.log(f"API process killed", "WARNING")
            except Exception as e:
                self.log(f"Error stopping API: {e}", "WARNING")
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                self.log(f"Dashboard process stopped", "INFO")
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
                self.log(f"Dashboard process killed", "WARNING")
            except Exception as e:
                self.log(f"Error stopping dashboard: {e}", "WARNING")
    
    def run_complete_test(self) -> bool:
        """Run complete test suite"""
        try:
            self.log("="*80)
            self.log("AIPMS DASHBOARD COMPLETE TEST SUITE", "INFO")
            self.log("="*80)
            
            # Step 1: Start API
            self.log("\n[STEP 1/4] Starting API...", "INFO")
            if not self.start_api():
                self.log("Cannot proceed without API", "ERROR")
                return False
            
            time.sleep(2)  # Let API settle
            
            # Step 2: Start Dashboard
            self.log("\n[STEP 2/4] Starting Dashboard...", "INFO")
            if not self.start_dashboard():
                self.log("Warning: Dashboard failed to start", "WARNING")
            
            time.sleep(3)  # Let dashboard settle
            
            # Step 3: Run Integration Tests
            self.log("\n[STEP 3/4] Running Integration Tests...", "INFO")
            test_success = self.run_integration_tests()
            
            # Step 4: Run Pytest
            self.log("\n[STEP 4/4] Running Pytest Suite...", "INFO")
            pytest_success = self.run_pytest()
            
            # Final Report
            self.log("\n" + "="*80, "INFO")
            self.log("TEST SUMMARY", "INFO")
            self.log("="*80, "INFO")
            
            if test_success and pytest_success:
                self.log("✓ ALL TESTS PASSED", "SUCCESS")
                return True
            else:
                self.log("✗ SOME TESTS FAILED", "ERROR")
                if not test_success:
                    self.log("  - Integration tests failed", "ERROR")
                if not pytest_success:
                    self.log("  - Pytest failed", "ERROR")
                return False
        
        finally:
            self.log("\n[CLEANUP] Stopping services...", "INFO")
            self.stop_services()
            self.log("Test suite complete", "INFO")


def main():
    """Main entry point"""
    runner = TestRunner()
    
    # Set up signal handlers for clean shutdown
    def signal_handler(signum, frame):
        runner.log("Received interrupt signal, cleaning up...", "WARNING")
        runner.stop_services()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run tests
    success = runner.run_complete_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
