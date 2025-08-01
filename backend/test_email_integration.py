#!/usr/bin/env python
"""
Simple integration test for email communication system.
This tests the core functionality without running the full test suite.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.development')
django.setup()

from accounts.models import School, SchoolEmailTemplate, EmailTemplateType
from accounts.services.default_templates import DefaultEmailTemplates
from accounts.services.email_template_service import EmailTemplateRenderingService


def test_basic_functionality():
    """Test basic email system functionality."""
    print("Testing basic email communication system functionality...")
    
    # Test 1: Default template creation
    print("1. Testing default template creation...")
    try:
        template_data = DefaultEmailTemplates.get_default_template(EmailTemplateType.INVITATION)
        assert 'name' in template_data
        assert 'subject' in template_data
        assert 'html' in template_data
        assert 'text' in template_data
        print("   ✓ Default template creation works")
    except Exception as e:
        print(f"   ✗ Default template creation failed: {e}")
        return False
    
    # Test 2: School and template creation
    print("2. Testing school and template creation...")
    try:
        # Create a test school
        school, created = School.objects.get_or_create(
            name="Test Integration School",
            defaults={
                'description': 'A school for integration testing',
                'contact_email': 'test@integration.com',
                'primary_color': '#4CAF50'
            }
        )
        
        # Create a template for the school
        template, created = SchoolEmailTemplate.objects.get_or_create(
            school=school,
            template_type=EmailTemplateType.INVITATION,
            defaults={
                'name': 'Test Invitation Template',
                'subject_template': 'Join {{ school_name }} - {{ teacher_name }}',
                'html_content': '<h1>Welcome {{ teacher_name }}!</h1><p>Join {{ school_name }}</p>',
                'text_content': 'Welcome {{ teacher_name }}! Join {{ school_name }}',
                'use_school_branding': True
            }
        )
        print("   ✓ School and template creation works")
    except Exception as e:
        print(f"   ✗ School and template creation failed: {e}")
        return False
    
    # Test 3: Template rendering
    print("3. Testing template rendering...")
    try:
        context = {
            'teacher_name': 'John Doe',
            'recipient_email': 'john@example.com'
        }
        
        subject, html_content, text_content = EmailTemplateRenderingService.render_template(
            template=template,
            context_variables=context
        )
        
        assert 'John Doe' in subject
        assert 'Test Integration School' in subject
        assert 'John Doe' in html_content
        assert 'Test Integration School' in html_content
        print("   ✓ Template rendering works")
    except Exception as e:
        print(f"   ✗ Template rendering failed: {e}")
        return False
    
    # Test 4: School branding integration
    print("4. Testing school branding integration...")
    try:
        # Check that school colors are in the rendered HTML
        assert school.primary_color in html_content
        assert '--school-primary-color' in html_content
        print("   ✓ School branding integration works")
    except Exception as e:
        print(f"   ✗ School branding integration failed: {e}")
        return False
    
    print("\n🎉 All basic tests passed! Email communication system is working correctly.")
    return True


def test_all_template_types():
    """Test that all template types can be created and rendered."""
    print("\nTesting all template types...")
    
    for template_type_tuple in EmailTemplateType.choices:
        template_type = template_type_tuple[0]
        template_display = template_type_tuple[1]
        
        try:
            template_data = DefaultEmailTemplates.get_default_template(template_type)
            print(f"   ✓ {template_display} template created successfully")
        except Exception as e:
            print(f"   ✗ {template_display} template failed: {e}")
            return False
    
    print("   ✓ All template types work correctly")
    return True


if __name__ == '__main__':
    print("Email Communication System Integration Test")
    print("=" * 50)
    
    success = test_basic_functionality()
    if success:
        success = test_all_template_types()
    
    if success:
        print("\n🚀 Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)