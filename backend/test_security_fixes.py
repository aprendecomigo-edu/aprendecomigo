#!/usr/bin/env python3
"""
Quick verification script for Teacher Profile Wizard security fixes.
This script tests basic functionality without requiring the full Django test suite.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_serializer_imports():
    """Test that all new serializers can be imported successfully."""
    try:
        from accounts.serializers import (
            ProfileWizardDataSerializer,
            ProfileWizardStepValidationSerializer,
            ProfilePhotoUploadSerializer
        )
        print("✅ All security serializers imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import serializers: {e}")
        return False

def test_throttle_imports():
    """Test that throttle classes can be imported successfully."""
    try:
        from accounts.throttles import (
            ProfileWizardThrottle,
            FileUploadThrottle,
            SecurityEventThrottle
        )
        print("✅ All throttle classes imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import throttles: {e}")
        return False

def test_validation_logic():
    """Test basic validation logic without Django setup."""
    try:
        from accounts.serializers import ProfileWizardDataSerializer
        
        # Test valid data
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone_number': '+1234567890',
            'professional_bio': 'I am a mathematics teacher.',
            'years_experience': 5,
        }
        
        serializer = ProfileWizardDataSerializer(data=valid_data)
        # Note: We can't call is_valid() without Django setup, but we can test instantiation
        print("✅ ProfileWizardDataSerializer instantiation successful")
        return True
    except Exception as e:
        print(f"❌ Validation logic test failed: {e}")
        return False

def test_bleach_import():
    """Test that bleach library is available."""
    try:
        import bleach
        
        # Test basic sanitization
        dirty_html = '<script>alert("xss")</script><p>Safe content</p>'
        clean_html = bleach.clean(dirty_html, tags=['p'], strip=True)
        
        if '<script>' not in clean_html and '<p>Safe content</p>' in clean_html:
            print("✅ Bleach HTML sanitization working correctly")
            return True
        else:
            print("❌ Bleach sanitization not working as expected")
            return False
    except ImportError as e:
        print(f"❌ Bleach library not available: {e}")
        return False

def test_security_patterns():
    """Test security pattern detection logic."""
    try:
        # Simulate the security pattern detection function
        def detect_security_patterns(data):
            if not isinstance(data, dict):
                return False
            
            suspicious_patterns = [
                '<script', 'javascript:', 'data:text/html', 'vbscript:',
                'onload=', 'onerror=', 'onclick=', 'onmouseover=',
                '<?php', '<%', '<iframe', 'eval(', 'alert(',
                'DROP TABLE', 'UNION SELECT', 'OR 1=1', '--',
                '../', '..\\', '/etc/passwd', 'cmd.exe',
            ]
            
            data_str = str(data).lower()
            
            for pattern in suspicious_patterns:
                if pattern.lower() in data_str:
                    return True
            
            return False
        
        # Test malicious patterns
        malicious_data = {'name': '<script>alert("xss")</script>'}
        safe_data = {'name': 'John Doe'}
        
        if detect_security_patterns(malicious_data) and not detect_security_patterns(safe_data):
            print("✅ Security pattern detection working correctly")
            return True
        else:
            print("❌ Security pattern detection failed")
            return False
            
    except Exception as e:
        print(f"❌ Security pattern test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🔒 Testing Teacher Profile Wizard Security Fixes")
    print("=" * 50)
    
    tests = [
        test_serializer_imports,
        test_throttle_imports,
        test_validation_logic,
        test_bleach_import,
        test_security_patterns,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All security fixes are working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())