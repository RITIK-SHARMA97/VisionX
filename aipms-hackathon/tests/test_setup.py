"""
Test suite for Phase 1: Setup & Scaffolding verification
"""
import os
import sqlite3
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

class TestPhase1Setup:
    """Phase 1 verification tests"""
    
    def test_project_structure_exists(self):
        """Verify all required directories exist"""
        directories = [
            'data/raw', 'data/processed', 'data/scalers',
            'models/train', 'models/saved',
            'simulator', 'api', 'api/models', 'api/routes',
            'dashboard', 'dashboard/pages', 'dashboard/components',
            'tests', 'config', 'logs'
        ]
        
        for dir_path in directories:
            full_path = PROJECT_ROOT / dir_path
            assert full_path.exists(), f"Directory missing: {dir_path}"
            assert full_path.is_dir(), f"Not a directory: {dir_path}"
        
        print("✅ All directories exist")
    
    def test_requirements_file_exists(self):
        """Verify requirements.txt exists and contains key packages"""
        req_file = PROJECT_ROOT / 'requirements.txt'
        assert req_file.exists(), "requirements.txt not found"
        
        content = req_file.read_text()
        required_packages = [
            'pandas', 'numpy', 'scikit-learn', 'xgboost', 'torch',
            'streamlit', 'plotly', 'fastapi', 'uvicorn', 'sqlalchemy',
            'paho-mqtt', 'apscheduler', 'pytest'
        ]
        
        for package in required_packages:
            assert package in content.lower(), f"Package {package} not in requirements.txt"
        
        print("✅ requirements.txt valid with all key packages")
    
    def test_env_file_exists(self):
        """Verify .env and .env.example files exist"""
        env_file = PROJECT_ROOT / '.env'
        env_example = PROJECT_ROOT / '.env.example'
        
        assert env_file.exists(), ".env not found"
        assert env_example.exists(), ".env.example not found"
        
        print("✅ Environment files exist")
    
    def test_database_schema_exists(self):
        """Verify database schema.sql exists with required tables"""
        schema_file = PROJECT_ROOT / 'config' / 'schema.sql'
        assert schema_file.exists(), "schema.sql not found"
        
        content = schema_file.read_text()
        required_tables = [
            'equipment', 'sensor_readings', 'predictions',
            'alerts', 'maintenance_jobs'
        ]
        
        for table in required_tables:
            assert f'CREATE TABLE' in content and table in content, f"Table {table} not in schema"
        
        print("✅ Database schema valid with all required tables")
    
    def test_python_imports(self):
        """Verify key Python modules can be imported (stubs)"""
        try:
            from api.models.orm import Equipment
            from api.models.schema import EquipmentResponse
            print("✅ API models import successfully")
        except ImportError as e:
            pytest.skip(f"ORM import requires dependencies: {e}")
    
    def test_mosquitto_config_exists(self):
        """Verify Mosquitto MQTT configuration exists"""
        config_file = PROJECT_ROOT / 'config' / 'mosquitto.conf'
        assert config_file.exists(), "mosquitto.conf not found"
        
        content = config_file.read_text()
        assert 'listener 1883' in content, "MQTT listener not configured"
        
        print("✅ Mosquitto configuration exists")
    
    def test_startup_scripts_exist(self):
        """Verify startup scripts exist"""
        scripts = ['start.ps1', 'start.sh']
        
        for script in scripts:
            script_file = PROJECT_ROOT / script
            assert script_file.exists(), f"{script} not found"
        
        print("✅ Startup scripts exist")
    
    def test_gitignore_exists(self):
        """Verify .gitignore exists and ignores sensitive files"""
        gitignore = PROJECT_ROOT / '.gitignore'
        assert gitignore.exists(), ".gitignore not found"
        
        content = gitignore.read_text()
        assert '.env' in content, ".env not in .gitignore"
        assert '*.db' in content, "*.db not in .gitignore"
        assert '__pycache__' in content, "__pycache__ not in .gitignore"
        
        print("✅ .gitignore properly configured")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
