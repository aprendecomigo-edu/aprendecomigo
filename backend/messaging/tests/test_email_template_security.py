"""
Business security tests for email template system.

Critical business security requirements:
- Template injection prevention (server compromise protection)
- XSS prevention (user safety)
- Input validation (data integrity)
- Access control (tenant isolation)
- Template size limits (resource protection)
"""

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
from messaging.tests.test_base import MessagingTestBase, SecurityTestMixin

User = get_user_model()


class SecureTemplateEngineTest(TestCase, SecurityTestMixin):
    """Test the secure template engine security validations."""
    
    def setUp(self):
        self.safe_template = "Hello {{ name }}, welcome to {{ school_name }}!"
        self.safe_context = {
            'name': 'John Doe',
            'school_name': 'Test School'
        }
    
    def test_safe_template_rendering_produces_expected_output(self):
        """Test business rule: safe templates render correctly without security issues."""
        result = SecureTemplateEngine.render_template(
            self.safe_template, self.safe_context
        )
        self.assertEqual(result, "Hello John Doe, welcome to Test School!")
    
    def test_template_injection_attack_prevention(self):
        """Test business security rule: prevent server compromise through template injection."""
        attack_vectors = [
            "{{ ''.__class__.__mro__[1].__subclasses__() }}",  # Python introspection
            "{% load os %}{{ os.system('ls') }}",              # OS command execution
            "{{ request.META }}",                              # Server information leak
            "{{ settings.SECRET_KEY }}",                       # Credential theft
            "{% import os %}",                                 # Module import
            "{{ eval('__import__(\"os\").system(\"ls\")') }}", # Code evaluation
            "{{ __import__('os').system('whoami') }}",         # Direct system access
        ]
        
        for attack_vector in attack_vectors:
            with self.subTest(attack_vector=attack_vector):
                # Business threat: malicious users attempting server compromise
                with self.assertRaises(ValidationError):
                    SecureTemplateEngine.validate_template_content(attack_vector)
    
    def test_system_access_template_tag_blocking(self):
        """Test business security rule: block template tags that access system resources."""
        attack_vectors = [
            "{% load subprocess %}",        # Process execution
            "{% load os %}",               # Operating system access
            "{% include '/etc/passwd' %}",  # Sensitive file access
            "{% extends '/etc/hosts' %}",   # System configuration access
            "{% ssi '/etc/passwd' %}",      # Server-side include attacks
            "{% cycle 'eval' %}",          # Code evaluation
        ]
        
        for attack_vector in attack_vectors:
            with self.subTest(attack_vector=attack_vector):
                # Business threat: unauthorized system resource access
                with self.assertRaises(ValidationError):
                    SecureTemplateEngine.validate_template_content(attack_vector)
    
    def test_dangerous_filter_blocking(self):
        """Test business security rule: dangerous template filters are blocked."""
        dangerous_filters = [
            "{{ name|exec }}",
            "{{ name|eval }}",
            "{{ name|import }}",
            "{{ name|subprocess }}",
        ]
        
        for dangerous_filter in dangerous_filters:
            with self.subTest(dangerous_filter=dangerous_filter):
                # Business threat: code execution through template filters
                with self.assertRaises(ValidationError):
                    SecureTemplateEngine.validate_template_content(dangerous_filter)
    
    def test_template_size_limit_enforcement(self):
        """Test business rule: templates exceeding size limits are rejected to prevent DoS."""
        large_template = "x" * (SecureTemplateEngine.MAX_TEMPLATE_SIZE + 1)
        
        with self.assertRaises(ValidationError):
            SecureTemplateEngine.validate_template_content(large_template)
    
    def test_nesting_depth_limit_enforcement(self):
        """Test business rule: deeply nested templates are rejected to prevent stack overflow."""
        # Create a template with excessive nesting
        nested_template = ""
        for i in range(SecureTemplateEngine.MAX_NESTING_DEPTH + 1):
            nested_template += "{% if true %}"
        nested_template += "content"
        for i in range(SecureTemplateEngine.MAX_NESTING_DEPTH + 1):
            nested_template += "{% endif %}"
        
        with self.assertRaises(ValidationError):
            SecureTemplateEngine.validate_template_content(nested_template)
    
    def test_context_variable_sanitization(self):
        """Test business rule: context variables are properly sanitized to prevent XSS."""
        malicious_context = {
            'safe_var': 'safe_value',
            'xss_var': '<script>alert("xss")</script>',
            'html_var': '<b>bold</b>',
            '__dangerous__': 'should_be_removed',
            'eval': lambda: 'dangerous',
        }
        
        sanitized = SecureTemplateEngine.sanitize_context_variables(malicious_context)
        
        # Business rule: safe variables remain unchanged
        self.assertEqual(sanitized['safe_var'], 'safe_value')
        
        # Business rule: XSS content is escaped
        self.assert_content_escaped(sanitized['xss_var'], malicious_context['xss_var'])
        
        # Business rule: dangerous variable names are removed
        self.assertNotIn('__dangerous__', sanitized)
        self.assertNotIn('eval', sanitized)


class HTMLSanitizerTest(TestCase, SecurityTestMixin):
    """Test HTML sanitization for XSS prevention."""
    
    def test_safe_html_content_preservation(self):
        """Test business rule: safe HTML content is preserved for user experience."""
        safe_html = "<p>Hello <strong>world</strong>!</p>"
        result = HTMLSanitizer.sanitize_html(safe_html)
        self.assertIn("<p>", result)
        self.assertIn("<strong>", result)
    
    def test_malicious_html_removal(self):
        """Test business rule: malicious HTML patterns are removed to prevent XSS."""
        test_cases = [
            ("<p>Hello</p><script>alert('xss')</script><p>World</p>", "<script>"),
            ('<div onclick="alert(\'xss\')" onload="badFunction()">Content</div>', "onclick"),
            ('<a href="javascript:alert(\'xss\')">Click me</a>', "javascript:"),
            ('<div style="background: expression(alert(\'xss\'))">Content</div>', "expression"),
        ]
        
        for malicious_html, dangerous_pattern in test_cases:
            with self.subTest(malicious_html=malicious_html, dangerous_pattern=dangerous_pattern):
                result = HTMLSanitizer.sanitize_html(malicious_html)
                self.assertNotIn(dangerous_pattern.lower(), result.lower())


class TemplateVariableValidatorTest(TestCase, SecurityTestMixin):
    """Test template variable validation for security."""
    
    def test_safe_context_validation_passes(self):
        """Test business rule: safe context variables pass validation."""
        safe_context = {
            'name': 'John Doe',
            'age': 25,
            'active': True,
            'tags': ['student', 'premium'],
            'profile': {'email': 'john@example.com'}
        }
        
        # Should not raise an exception
        TemplateVariableValidator.validate_context(safe_context)
    
    def test_callable_object_rejection(self):
        """Test business rule: callable objects are rejected to prevent code execution."""
        dangerous_context = {
            'name': 'John',
            'dangerous_func': lambda: 'bad',
        }
        
        with self.assertRaises(ValidationError):
            TemplateVariableValidator.validate_context(dangerous_context)
    
    def test_oversized_string_rejection(self):
        """Test business rule: oversized strings are rejected to prevent DoS."""
        large_string = "x" * (TemplateVariableValidator.MAX_STRING_LENGTH + 1)
        dangerous_context = {
            'large_value': large_string
        }
        
        with self.assertRaises(ValidationError):
            TemplateVariableValidator.validate_context(dangerous_context)
    
    def test_deep_object_nesting_rejection(self):
        """Test business rule: deeply nested objects are rejected to prevent stack overflow."""
        deep_object = {}
        current = deep_object
        
        for i in range(TemplateVariableValidator.MAX_OBJECT_DEPTH + 1):
            current['nested'] = {}
            current = current['nested']
        
        with self.assertRaises(ValidationError):
            TemplateVariableValidator.validate_context({'deep': deep_object})


class EmailTemplateModelSecurityTest(MessagingTestBase, SecurityTestMixin):
    """Test email template model security validation."""
    
    def test_safe_template_creation_succeeds(self):
        """Test business rule: safe templates can be created without security violations."""
        template = SchoolEmailTemplate(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Safe Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Hello {{ name }}, welcome to {{ school_name }}!</p>",
            text_content="Hello {{ name }}, welcome to {{ school_name }}!",
            created_by=self.admin_user
        )
        
        # Should not raise an exception
        template.full_clean()
        template.save()
        self.assertTrue(template.pk)
    
    def test_malicious_template_rejection(self):
        """Test business rule: malicious templates are rejected to protect platform security."""
        template = SchoolEmailTemplate(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Malicious Template",
            subject_template="Welcome {{ name }}!",
            html_content="<script>alert('xss')</script>{{ __import__('os').system('ls') }}",
            text_content="Safe text",
            created_by=self.admin_user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()
    
    def test_malicious_css_rejection(self):
        """Test business rule: malicious CSS is rejected to prevent style-based attacks."""
        template = SchoolEmailTemplate(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="CSS Attack Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Safe content</p>",
            text_content="Safe text",
            custom_css="body { background: expression(alert('xss')); }",
            created_by=self.admin_user
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()


class EmailTemplateAPISecurityTest(APITestCase, SecurityTestMixin):
    """Test API security for email template operations."""
    
    def setUp(self):
        # Create schools and users
        self.school = School.objects.create(
            name="Test School",
            description="A test school for security testing"
        )
        self.other_school, self.other_user = self._create_other_school()
        
        # Create main user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        # Create school memberships
        from accounts.models import SchoolMembership, SchoolRole
        SchoolMembership.objects.create(
            user=self.user,
            school=self.school,
            role=SchoolRole.SCHOOL_OWNER
        )
        
        # Create tokens for authentication
        self.token = Token.objects.create(user=self.user)
        self.other_token = Token.objects.create(user=self.other_user)
        
        self.client = APIClient()
    
    def _create_other_school(self):
        """Create another school for cross-tenant testing."""
        other_school = School.objects.create(
            name="Other School",
            description="Another test school"
        )
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )
        from accounts.models import SchoolMembership, SchoolRole
        SchoolMembership.objects.create(
            user=other_user,
            school=other_school,
            role=SchoolRole.SCHOOL_OWNER
        )
        return other_school, other_user
    
    def test_authentication_required_for_template_operations(self):
        """Test business rule: authentication is required for all template operations."""
        url = reverse('schoolemailtemplate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_school_isolation_in_template_access(self):
        """Test business rule: users can only access their own school's templates."""
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
    
    def test_malicious_template_creation_blocked_via_api(self):
        """Test business rule: malicious templates cannot be created via API."""
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
    
    def test_cross_school_template_access_denied(self):
        """Test business rule: users cannot access templates from other schools."""
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


class EmailTemplateRenderingSecurityTest(MessagingTestBase, SecurityTestMixin):
    """Test security of email template rendering service."""
    
    def setUp(self):
        super().setUp()
        self.template = SchoolEmailTemplate.objects.create(
            school=self.school,
            template_type=EmailTemplateType.WELCOME,
            name="Test Template",
            subject_template="Welcome {{ name }}!",
            html_content="<p>Hello {{ name }}, welcome to {{ school_name }}!</p>",
            text_content="Hello {{ name }}, welcome to {{ school_name }}!",
            created_by=self.admin_user
        )
    
    def test_safe_template_rendering_includes_context(self):
        """Test business rule: safe templates render correctly with provided context."""
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
    
    def test_xss_prevention_in_template_variables(self):
        """Test business rule: XSS in variables is prevented during rendering."""
        context = {
            'name': '<script>alert("xss")</script>',
            'message': '<img src=x onerror=alert(1)>'
        }
        
        subject, html_content, text_content = EmailTemplateRenderingService.render_template(
            self.template, context
        )
        
        # Business security rule: XSS content is escaped
        self.assert_content_escaped(html_content, context['name'])
    
    def test_malicious_context_rejection(self):
        """Test business rule: malicious context variables are rejected."""
        malicious_context = {
            'name': 'John',
            'dangerous_func': lambda: 'bad',
            '__import__': __import__,
        }
        
        with self.assertRaises(ValueError):
            EmailTemplateRenderingService.render_template(
                self.template, malicious_context
            )


class SecurityRegressionTest(MessagingTestBase, SecurityTestMixin):
    """Test for security regression prevention."""
    
    def test_known_attack_vectors_blocked_in_subject(self):
        """Test business security rule: known attack vectors are blocked in subject templates."""
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
        
        for attack_vector in attack_vectors:
            with self.subTest(attack_vector=attack_vector):
                with self.assertRaises(ValidationError):
                    template = SchoolEmailTemplate(
                        school=self.school,
                        template_type=EmailTemplateType.WELCOME,
                        name="Test",
                        subject_template=attack_vector,
                        html_content="Safe content",
                        text_content="Safe content",
                        created_by=self.admin_user
                    )
                    template.full_clean()
    
    def test_known_attack_vectors_blocked_in_html_content(self):
        """Test business security rule: known attack vectors are blocked in HTML content."""
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
        
        for attack_vector in attack_vectors:
            with self.subTest(attack_vector=attack_vector):
                with self.assertRaises(ValidationError):
                    template = SchoolEmailTemplate(
                        school=self.school,
                        template_type=EmailTemplateType.WELCOME,
                        name="Test",
                        subject_template="Safe subject",
                        html_content=attack_vector,
                        text_content="Safe content",
                        created_by=self.admin_user
                    )
                    template.full_clean()
    
    def test_security_bypass_edge_cases_handled(self):
        """Test business security rule: edge cases that might bypass security filters are handled."""
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
                        created_by=self.admin_user
                    )
                    template.full_clean()
                    
                    # If validation passes, ensure rendering is safe
                    context = {'name': 'Test'}
                    subject, html_content, text_content = EmailTemplateRenderingService.render_template(
                        template, context
                    )
                    
                    # Business security rule: no executable content remains
                    self.assertNotIn('<script', html_content.lower())
                    self.assertNotIn('javascript:', html_content.lower())
                    
                except ValidationError:
                    # Validation rejection is also acceptable
                    pass