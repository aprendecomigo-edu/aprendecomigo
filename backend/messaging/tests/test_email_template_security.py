"""
Business security tests for email template system.

Critical business security requirements:
- Template injection prevention (server compromise protection)
- XSS prevention (user safety)
- Input validation (data integrity)
- Access control (tenant isolation)
- Template size limits (resource protection)
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from accounts.models import School, SchoolRole
from messaging.models import SchoolEmailTemplate, EmailTemplateType
from messaging.services.secure_template_engine import (
    SecureTemplateEngine, HTMLSanitizer, TemplateVariableValidator
)
from messaging.services.email_template_service import EmailTemplateRenderingService

User = get_user_model()


class SecureTemplateEngineTest(TestCase):
    """Test the secure template engine security validations."""
    
    def setUp(self):
        self.safe_template = "Hello {{ name }}, welcome to {{ school_name }}!"
        self.safe_context = {
            'name': 'John Doe',
            'school_name': 'Test School'
        }
    
    def test_safe_template_rendering(self):
        """Test that safe templates render correctly."""
        result = SecureTemplateEngine.render_template(
            self.safe_template, self.safe_context
        )
        self.assertEqual(result, "Hello John Doe, welcome to Test School!")
    
    def test_prevent_server_compromise_via_template_injection(self):
        """Test business security rule: prevent server compromise through template injection."""
        # Business threat: malicious users attempting server compromise
        server_compromise_attempts = [
            "{{ ''.__class__.__mro__[1].__subclasses__() }}",  # Python introspection
            "{% load os %}{{ os.system('ls') }}",              # OS command execution
            "{{ request.META }}",                              # Server information leak
            "{{ settings.SECRET_KEY }}",                       # Credential theft
            "{% import os %}",                                 # Module import
            "{{ eval('__import__(\"os\").system(\"ls\")') }}",  # Code evaluation
            "{{ __import__('os').system('whoami') }}",         # Direct system access
        ]
        
        for attack_vector in server_compromise_attempts:
            with self.subTest(attack_vector=attack_vector):
                with self.assertRaises(ValidationError):
                    SecureTemplateEngine.validate_template_content(attack_vector)
    
    def test_block_system_access_template_tags(self):
        """Test business security rule: block template tags that access system resources."""
        # Business threat: unauthorized system resource access
        system_access_attempts = [
            "{% load subprocess %}",        # Process execution
            "{% load os %}",               # Operating system access
            "{% include '/etc/passwd' %}",  # Sensitive file access
            "{% extends '/etc/hosts' %}",   # System configuration access
            "{% ssi '/etc/passwd' %}",      # Server-side include attacks
            "{% cycle 'eval' %}",          # Code evaluation
        ]
        
        for attack_vector in system_access_attempts:
            with self.subTest(attack_vector=attack_vector):
                with self.assertRaises(ValidationError):
                    SecureTemplateEngine.validate_template_content(attack_vector)
    
    def test_dangerous_filter_prevention(self):
        """Test that dangerous template filters are blocked."""
        dangerous_templates = [
            "{{ name|exec }}",
            "{{ name|eval }}",
            "{{ name|import }}",
            "{{ name|subprocess }}",
        ]
        
        for template in dangerous_templates:
            with self.subTest(template=template):
                with self.assertRaises(ValidationError):
                    SecureTemplateEngine.validate_template_content(template)
    
    def test_template_size_limit(self):
        """Test that templates exceeding size limits are rejected."""
        large_template = "x" * (SecureTemplateEngine.MAX_TEMPLATE_SIZE + 1)
        
        with self.assertRaises(ValidationError):
            SecureTemplateEngine.validate_template_content(large_template)
    
    def test_nesting_depth_limit(self):
        """Test that deeply nested templates are rejected."""
        # Create a template with excessive nesting
        nested_template = ""
        for i in range(SecureTemplateEngine.MAX_NESTING_DEPTH + 1):
            nested_template += "{% if true %}"
        nested_template += "content"
        for i in range(SecureTemplateEngine.MAX_NESTING_DEPTH + 1):
            nested_template += "{% endif %}"
        
        with self.assertRaises(ValidationError):
            SecureTemplateEngine.validate_template_content(nested_template)
    
    def test_context_sanitization(self):
        """Test that context variables are properly sanitized."""
        malicious_context = {
            'safe_var': 'safe_value',
            'xss_var': '<script>alert("xss")</script>',
            'html_var': '<b>bold</b>',
            '__dangerous__': 'should_be_removed',
            'eval': lambda: 'dangerous',
        }
        
        sanitized = SecureTemplateEngine.sanitize_context_variables(malicious_context)
        
        # Safe variables should remain
        self.assertEqual(sanitized['safe_var'], 'safe_value')
        
        # XSS should be escaped
        self.assertIn('&lt;script&gt;', sanitized['xss_var'])
        
        # HTML should be escaped
        self.assertIn('&lt;b&gt;', sanitized['html_var'])
        
        # Dangerous names should be removed
        self.assertNotIn('__dangerous__', sanitized)
        self.assertNotIn('eval', sanitized)


class HTMLSanitizerTest(TestCase):
    """Test HTML sanitization for XSS prevention."""
    
    def test_safe_html_preservation(self):
        """Test that safe HTML is preserved."""
        safe_html = "<p>Hello <strong>world</strong>!</p>"
        result = HTMLSanitizer.sanitize_html(safe_html)
        self.assertIn("<p>", result)
        self.assertIn("<strong>", result)
    
    def test_script_tag_removal(self):
        """Test that script tags are removed."""
        malicious_html = "<p>Hello</p><script>alert('xss')</script><p>World</p>"
        result = HTMLSanitizer.sanitize_html(malicious_html)
        self.assertNotIn("<script>", result)
        self.assertNotIn("alert", result)
        self.assertIn("<p>Hello</p>", result)
    
    def test_event_handler_removal(self):
        """Test that event handlers are removed."""
        malicious_html = '<div onclick="alert(\'xss\')" onload="badFunction()">Content</div>'
        result = HTMLSanitizer.sanitize_html(malicious_html)
        self.assertNotIn("onclick", result)
        self.assertNotIn("onload", result)
        self.assertIn("Content", result)
    
    def test_javascript_url_removal(self):
        """Test that javascript: URLs are removed."""
        malicious_html = '<a href="javascript:alert(\'xss\')">Click me</a>'
        result = HTMLSanitizer.sanitize_html(malicious_html)
        self.assertNotIn("javascript:", result)
    
    def test_dangerous_css_removal(self):
        """Test that dangerous CSS is removed."""
        malicious_html = '<div style="background: expression(alert(\'xss\'))">Content</div>'
        result = HTMLSanitizer.sanitize_html(malicious_html)
        self.assertNotIn("expression", result)


class TemplateVariableValidatorTest(TestCase):
    """Test template variable validation."""
    
    def test_safe_context_validation(self):
        """Test that safe context passes validation."""
        safe_context = {
            'name': 'John Doe',
            'age': 25,
            'active': True,
            'tags': ['student', 'premium'],
            'profile': {'email': 'john@example.com'}
        }
        
        # Should not raise an exception
        TemplateVariableValidator.validate_context(safe_context)
    
    def test_callable_rejection(self):
        """Test that callable objects are rejected."""
        dangerous_context = {
            'name': 'John',
            'dangerous_func': lambda: 'bad',
        }
        
        with self.assertRaises(ValidationError):
            TemplateVariableValidator.validate_context(dangerous_context)
    
    def test_oversized_string_rejection(self):
        """Test that oversized strings are rejected."""
        large_string = "x" * (TemplateVariableValidator.MAX_STRING_LENGTH + 1)
        dangerous_context = {
            'large_value': large_string
        }
        
        with self.assertRaises(ValidationError):
            TemplateVariableValidator.validate_context(dangerous_context)
    
    def test_deep_nesting_rejection(self):
        """Test that deeply nested objects are rejected."""
        deep_object = {}
        current = deep_object
        
        for i in range(TemplateVariableValidator.MAX_OBJECT_DEPTH + 1):
            current['nested'] = {}
            current = current['nested']
        
        with self.assertRaises(ValidationError):
            TemplateVariableValidator.validate_context({'deep': deep_object})


class EmailTemplateModelSecurityTest(TestCase):
    """Test email template model security validation."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.school = School.objects.create(
            name="Test School",
            description="A test school for security testing"
        )
        # Create school membership for the user
        from accounts.models import SchoolMembership, SchoolRole
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
    
    def test_safe_template_creation(self):
        """Test that safe templates can be created."""
        template = SchoolEmailTemplate(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Safe Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Hello {{ name }}, welcome to {{ school_name }}!</p>",
            text_content="Hello {{ name }}, welcome to {{ school_name }}!",
            created_by=self.user
        )
        
        # Should not raise an exception
        template.full_clean()
        template.save()
    
    def test_malicious_template_rejection(self):
        """Test that malicious templates are rejected."""
        template = SchoolEmailTemplate(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Malicious Template",
            subject_template="Welcome {{ name }}!",
            html_content="<script>alert('xss')</script>{{ __import__('os').system('ls') }}",
            text_content="Safe text",
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()
    
    def test_malicious_css_rejection(self):
        """Test that malicious CSS is rejected."""
        template = SchoolEmailTemplate(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="CSS Attack Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Safe content</p>",
            text_content="Safe text",
            custom_css="body { background: expression(alert('xss')); }",
            created_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()


class EmailTemplateAPISecurityTest(APITestCase):
    """Test API security for email template operations."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )
        
        self.school = School.objects.create(
            name="Test School",
            description="A test school for security testing"
        )
        self.other_school = School.objects.create(
            name="Other School",
            description="Another test school"
        )
        
        # Create school memberships
        from accounts.models import SchoolMembership, SchoolRole
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        SchoolMembership.objects.create(
            user=self.other_user,
            school=self.other_school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
        # Create tokens for authentication
        self.token = Token.objects.create(user=self.user)
        self.other_token = Token.objects.create(user=self.other_user)
        
        self.client = APIClient()
    
    def test_authenticated_access_required(self):
        """Test that authentication is required for template operations."""
        url = reverse('schoolemailtemplate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_school_access_control(self):
        """Test that users can only access their own school's templates."""
        # Create template for user's school
        template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Test Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Welcome {{ name }}!</p>",
            text_content="Welcome {{ name }}!",
            created_by=self.user
        )
        
        # User should see their template
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('schoolemailtemplate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Other user should not see it
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_malicious_template_creation_blocked(self):
        """Test that malicious templates cannot be created via API."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        malicious_data = {
            'school': self.school.id,
            'template_type': EmailTemplateType.WELCOME,
            'name': 'Malicious Template',
            'subject_template': 'Welcome!',
            'html_content': '<script>alert("xss")</script>{{ __import__("os").system("ls") }}',
            'text_content': 'Safe text',
        }
        
        url = reverse('schoolemailtemplate-list')
        response = self.client.post(url, malicious_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('security validation failed', str(response.data).lower())
    
    def test_template_preview_security(self):
        """Test that template preview validates variables securely."""
        template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Test Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Welcome {{ name }}!</p>",
            text_content="Welcome {{ name }}!",
            created_by=self.user
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Test with malicious variables
        malicious_variables = {
            'name': 'John',
            'dangerous_func': 'lambda: os.system("ls")',
            '__import__': '__import__',
        }
        
        url = reverse('schoolemailtemplate-preview', kwargs={'pk': template.pk})
        response = self.client.post(url, {
            'template_variables': malicious_variables
        }, format='json')
        
        # Should be rejected due to variable validation
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cross_school_template_access_denied(self):
        """Test that users cannot access templates from other schools."""
        other_template = SchoolEmailTemplate.objects.create(
            school=self.other_school,
            template_type=EmailTemplateType.WELCOME,
            name="Other Template",
            subject_template="Welcome!",
            html_content="<p>Welcome!</p>",
            text_content="Welcome!",
            created_by=self.other_user
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Try to access other user's template
        url = reverse('schoolemailtemplate-detail', kwargs={'pk': other_template.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to update other user's template
        response = self.client.patch(url, {'name': 'Hacked Template'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to delete other user's template
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EmailTemplateRenderingSecurityTest(TestCase):
    """Test security of email template rendering service."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.school = School.objects.create(
            name="Test School",
            description="A test school for security testing"
        )
        # Create school membership for the user
        from accounts.models import SchoolMembership, SchoolRole
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        self.template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Test Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Hello {{ name }}, welcome to {{ school_name }}!</p>",
            text_content="Hello {{ name }}, welcome to {{ school_name }}!",
            created_by=self.user
        )
    
    def test_safe_rendering(self):
        """Test that safe templates render correctly."""
        context = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        
        subject, html_content, text_content = EmailTemplateRenderingService.render_template(
            self.template, context
        )
        
        self.assertIn('John Doe', subject)
        self.assertIn('John Doe', html_content)
        self.assertIn('John Doe', text_content)
        self.assertIn('Test School', html_content)  # School name from context
    
    def test_xss_prevention_in_variables(self):
        """Test that XSS in variables is prevented."""
        context = {
            'name': '<script>alert("xss")</script>',
            'message': '<img src=x onerror=alert(1)>'
        }
        
        subject, html_content, text_content = EmailTemplateRenderingService.render_template(
            self.template, context
        )
        
        # XSS should be escaped
        self.assertNotIn('<script>', html_content)
        self.assertNotIn('onerror=', html_content)
        self.assertIn('&lt;script&gt;', html_content)
    
    def test_malicious_context_rejection(self):
        """Test that malicious context is rejected."""
        malicious_context = {
            'name': 'John',
            'dangerous_func': lambda: 'bad',
            '__import__': __import__,
        }
        
        with self.assertRaises(ValueError):
            EmailTemplateRenderingService.render_template(
                self.template, malicious_context
            )


class SecurityRegressionTest(TestCase):
    """Test for security regression prevention."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.school = School.objects.create(
            name="Test School",
            description="A test school for security testing"
        )
        # Create school membership for the user
        from accounts.models import SchoolMembership, SchoolRole
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
    
    def test_known_attack_vectors(self):
        """Test known attack vectors to prevent regression."""
        attack_vectors = [
            # Template injection
            "{{ ''.__class__.__mro__[1].__subclasses__() }}",
            "{% load os %}{{ os.system('ls') }}",
            "{{ request.user.password }}",
            
            # XSS
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            
            # CSS injection
            "body { background: expression(alert('xss')); }",
            "@import url('javascript:alert(1)');",
            
            # Command injection attempts
            "; rm -rf /",
            "$(whoami)",
            "`ls -la`",
        ]
        
        for attack in attack_vectors:
            with self.subTest(attack=attack):
                # Try in subject
                with self.assertRaises(ValidationError):
                    template = SchoolEmailTemplate(
                        school=self.school,
                        template_type=EmailTemplateType.WELCOME,
                        name="Test",
                        subject_template=attack,
                        html_content="Safe content",
                        text_content="Safe content",
                        created_by=self.user
                    )
                    template.full_clean()
                
                # Try in HTML content
                with self.assertRaises(ValidationError):
                    template = SchoolEmailTemplate(
                        school=self.school,
                        template_type=EmailTemplateType.WELCOME,
                        name="Test",
                        subject_template="Safe subject",
                        html_content=attack,
                        text_content="Safe content",
                        created_by=self.user
                    )
                    template.full_clean()
    
    def test_edge_cases(self):
        """Test edge cases that might bypass security."""
        edge_cases = [
            # Unicode bypasses
            "\\u003cscript\\u003e",
            "\u003cscript\u003e",
            
            # Encoding bypasses
            "%3Cscript%3E",
            "&lt;script&gt;",
            
            # Case variations
            "<Script>",
            "<SCRIPT>",
            
            # Whitespace bypasses
            "< script >",
            "<\tscript>",
            "<\nscript>",
        ]
        
        for edge_case in edge_cases:
            with self.subTest(edge_case=edge_case):
                try:
                    template = SchoolEmailTemplate(
                        school=self.school,
                        template_type=EmailTemplateType.WELCOME,
                        name="Test",
                        subject_template="Safe subject",
                        html_content=f"<p>Content: {edge_case}</p>",
                        text_content="Safe content",
                        created_by=self.user
                    )
                    template.full_clean()
                    
                    # If validation passes, ensure rendering is safe
                    context = {'name': 'Test'}
                    subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                        template, context
                    )
                    
                    # Ensure no executable content remains
                    self.assertNotIn('<script', html_content.lower())
                    self.assertNotIn('javascript:', html_content.lower())
                    
                except ValidationError:
                    # Validation rejection is acceptable
                    pass