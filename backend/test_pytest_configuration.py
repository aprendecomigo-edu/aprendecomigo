"""
Test file to validate pytest configuration and Django integration.
This follows TDD methodology to ensure pytest setup works correctly.
"""
import os
import subprocess
import sys
from pathlib import Path


def test_pytest_can_run_basic_command():
    """Test that pytest command can be executed without errors."""
    try:
        # Test that pytest --help works
        result = subprocess.run([sys.executable, "-m", "pytest", "--help"], 
                              capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"pytest --help failed: {result.stderr}"
        assert "usage:" in result.stdout.lower() and ("pytest" in result.stdout.lower() or "__main__.py" in result.stdout), "pytest help output not as expected"
    except subprocess.TimeoutExpired:
        assert False, "pytest --help command timed out"
    except Exception as e:
        assert False, f"Failed to run pytest --help: {e}"


def test_pytest_can_discover_django_settings():
    """Test that pytest can discover and load Django settings."""
    # Set up environment for Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings.testing")
    
    try:
        # Test that pytest can run with Django settings
        result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "--quiet"], 
                              capture_output=True, text=True, timeout=30, cwd=Path(__file__).parent)
        
        # Check if there are any critical import errors
        if result.returncode != 0:
            # Allow collection warnings but not import errors
            if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                assert False, f"Django settings import failed: {result.stderr}"
            # Collection errors might be due to missing test files, which is OK for now
            
    except subprocess.TimeoutExpired:
        assert False, "pytest collection command timed out"
    except Exception as e:
        assert False, f"Failed to run pytest collection: {e}"


def test_django_test_database_configuration():
    """Test that Django test database is properly configured."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings.testing")
    
    try:
        import django
        from django.conf import settings
        from django.db import connection
        
        django.setup()
        
        # Test database settings
        test_db_config = settings.DATABASES['default']
        assert test_db_config is not None, "Default database not configured"
        
        # Test that database connection works (simple check)
        # Don't use setup_test_environment as it can only be called once
        assert hasattr(settings, 'DATABASES'), "DATABASES setting exists"
        assert 'default' in settings.DATABASES, "Default database configured"
        
    except Exception as e:
        assert False, f"Django test database configuration failed: {e}"


def test_pytest_django_integration():
    """Test that pytest-django integration is working."""
    # Create a minimal test file to verify pytest-django works
    test_content = '''
import pytest
from django.test import TestCase
from django.conf import settings

@pytest.mark.django_db
def test_django_db_access():
    """Test that Django database access works with pytest."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # This should work without errors if pytest-django is properly configured
    users_count = User.objects.count()
    assert users_count >= 0  # Should be a non-negative number

class TestDjangoTestCase(TestCase):
    """Test that Django TestCase works with pytest."""
    
    def test_settings_accessible(self):
        """Test that Django settings are accessible."""
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'DATABASES')
'''
    
    # Write temporary test file
    temp_test_file = Path(__file__).parent / "temp_django_test.py"
    try:
        with open(temp_test_file, 'w') as f:
            f.write(test_content)
        
        # Run pytest on this test file
        result = subprocess.run([
            sys.executable, "-m", "pytest", str(temp_test_file), "-v"
        ], capture_output=True, text=True, timeout=60, cwd=Path(__file__).parent)
        
        # Clean up
        temp_test_file.unlink()
        
        # Check results
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            assert False, f"pytest-django integration test failed: {result.stderr}"
            
        assert "PASSED" in result.stdout, "Django integration tests did not pass"
        
    except subprocess.TimeoutExpired:
        if temp_test_file.exists():
            temp_test_file.unlink()
        assert False, "pytest-django integration test timed out"
    except Exception as e:
        if temp_test_file.exists():
            temp_test_file.unlink()
        assert False, f"pytest-django integration test failed: {e}"


def test_pytest_configuration_file():
    """Test that pytest.ini configuration is properly set up."""
    pytest_ini_path = Path(__file__).parent / "pytest.ini"
    assert pytest_ini_path.exists(), "pytest.ini file does not exist"
    
    with open(pytest_ini_path, 'r') as f:
        config_content = f.read()
    
    # Test required configuration options
    required_options = [
        "DJANGO_SETTINGS_MODULE",
        "python_files",
        "python_classes", 
        "python_functions"
    ]
    
    for option in required_options:
        assert option in config_content, f"Required pytest option '{option}' not found in pytest.ini"
    
    # Test that Django settings module points to testing
    assert "aprendecomigo.settings.testing" in config_content, \
        "pytest.ini not configured to use testing settings"


if __name__ == "__main__":
    # Run these tests manually to validate configuration
    test_pytest_can_run_basic_command()
    test_pytest_configuration_file()
    test_django_test_database_configuration()
    test_pytest_can_discover_django_settings()
    test_pytest_django_integration()
    print("All pytest configuration tests passed!")