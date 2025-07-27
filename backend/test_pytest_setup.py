"""
Test file to validate pytest setup and dependencies.
This file tests the TDD approach for fixing the pytest configuration.
"""
import subprocess
import sys
import os
from pathlib import Path


def test_pytest_can_be_imported():
    """Test that pytest can be imported successfully."""
    try:
        import pytest
        assert pytest is not None
        print(f"pytest version: {pytest.__version__}")
    except ImportError as e:
        assert False, f"pytest cannot be imported: {e}"


def test_pytest_django_can_be_imported():
    """Test that pytest-django can be imported successfully."""
    try:
        import pytest_django
        assert pytest_django is not None
        print(f"pytest-django version: {pytest_django.__version__}")
    except ImportError as e:
        assert False, f"pytest-django cannot be imported: {e}"


def test_django_can_be_imported():
    """Test that Django can be imported successfully."""
    try:
        import django
        assert django is not None
        print(f"Django version: {django.__version__}")
    except ImportError as e:
        assert False, f"Django cannot be imported: {e}"


def test_requirements_file_exists():
    """Test that requirements.txt exists and is readable."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt file does not exist"
    assert requirements_path.is_file(), "requirements.txt is not a file"
    
    # Test that the file is readable
    with open(requirements_path, 'r') as f:
        content = f.read()
        assert len(content) > 0, "requirements.txt is empty"
        assert "pytest" in content, "pytest not found in requirements.txt"
        assert "pytest-django" in content, "pytest-django not found in requirements.txt"


def test_pytest_ini_exists_and_valid():
    """Test that pytest.ini exists and has valid configuration."""
    pytest_ini_path = Path(__file__).parent / "pytest.ini"
    assert pytest_ini_path.exists(), "pytest.ini file does not exist"
    
    with open(pytest_ini_path, 'r') as f:
        content = f.read()
        assert "[pytest]" in content, "pytest.ini missing [pytest] section"
        assert "DJANGO_SETTINGS_MODULE" in content, "pytest.ini missing DJANGO_SETTINGS_MODULE"
        assert "testing" in content, "pytest.ini not configured for testing settings"


def test_django_test_settings_exists():
    """Test that Django test settings module exists and is importable."""
    test_settings_path = Path(__file__).parent / "aprendecomigo" / "settings" / "testing.py"
    assert test_settings_path.exists(), "testing.py settings file does not exist"
    
    # Test that the settings module can be imported
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings.testing")
    try:
        import django
        from django.conf import settings
        django.setup()
        
        # Test critical settings for testing
        assert hasattr(settings, 'DATABASES'), "DATABASES setting not found"
        assert hasattr(settings, 'SECRET_KEY'), "SECRET_KEY setting not found"
        assert hasattr(settings, 'INSTALLED_APPS'), "INSTALLED_APPS setting not found"
        
        # Test that test database is configured
        test_db = settings.DATABASES['default']
        db_name = str(test_db.get('NAME', ''))
        db_engine = test_db.get('ENGINE', '')
        assert 'test' in db_name.lower() or 'sqlite3' in db_engine, \
            f"Test database not properly configured. NAME: {db_name}, ENGINE: {db_engine}"
            
    except Exception as e:
        assert False, f"Cannot import Django test settings: {e}"


if __name__ == "__main__":
    # Run these tests manually to validate setup
    test_requirements_file_exists()
    test_pytest_ini_exists_and_valid() 
    test_django_test_settings_exists()
    print("All basic setup tests passed!")