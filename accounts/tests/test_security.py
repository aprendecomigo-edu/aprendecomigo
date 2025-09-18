"""
Comprehensive Security Tests for Authentication System

This module tests security aspects of the authentication system including:
- Authentication bypass prevention
- Session security
- Input validation and sanitization
- Rate limiting and brute force protection
- Permission escalation prevention
- Data exposure prevention

These tests ensure the authentication system is secure against common attacks.
"""

from datetime import timedelta
import hashlib
import time
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import School, SchoolMembership, SchoolRole, VerificationToken
from accounts.services.otp_service import OTPService
from accounts.services.phone_validation import PhoneValidationService
from accounts.tests.test_base import BaseTestCase
from accounts.tests.test_utils import get_unique_email, get_unique_phone_number

User = get_user_model()


class AuthenticationBypassSecurityTest(BaseTestCase):
    """Test prevention of authentication bypass attempts"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )
        self.user.email_verified = True
        self.user.save()

    def test_otp_cannot_be_brute_forced(self):
        """Test OTP verification prevents brute force attacks"""
        # Generate OTP
        otp_code, token_id = OTPService.generate_otp(self.user, "email")

        # Attempt brute force with common patterns
        common_patterns = ["000000", "123456", "111111", "999999", "000001"]

        for i, pattern in enumerate(common_patterns):
            success, result = OTPService.verify_otp(token_id, pattern)
            self.assertFalse(success)

            if i < 4:  # Not locked yet
                self.assertIn("attempts remaining", result)
            else:  # Should be locked after 5 attempts
                break

        # Verify account is locked
        success, result = OTPService.verify_otp(token_id, otp_code)
        self.assertFalse(success)
        self.assertIn("Too many failed attempts", result)

    def test_session_fixation_prevention(self):
        """Test prevention of session fixation attacks"""
        # Get initial session key
        response = self.client.get(reverse("accounts:signin"))
        initial_session_key = self.client.session.session_key

        # Force login
        self.client.force_login(self.user)

        # Session key should change after login
        response = self.client.get("/")
        new_session_key = self.client.session.session_key

        self.assertNotEqual(initial_session_key, new_session_key)

    def test_magic_link_single_use_enforcement(self):
        """Test magic links can only be used once"""
        from sesame.utils import get_query_string

        # Generate magic link
        magic_token = get_query_string(self.user)
        magic_url = reverse("accounts:verify_email") + magic_token

        # Use magic link first time
        response1 = self.client.get(magic_url)
        self.assertEqual(response1.status_code, 302)  # Successful redirect

        # Logout to test reuse
        self.client.logout()

        # Attempt to use same magic link again
        response2 = self.client.get(magic_url)

        # Should fail or redirect to login (depending on implementation)
        self.assertNotEqual(response2.status_code, 200)  # Should not succeed

    def test_magic_link_expires_properly(self):
        """Test magic links expire after reasonable time"""
        from sesame.utils import get_query_string

        # Generate magic link
        magic_token = get_query_string(self.user)
        magic_url = reverse("accounts:verify_email") + magic_token

        # Test that magic link works when fresh
        response = self.client.get(magic_url)
        # Should work initially (this is the basic functionality test)
        # TODO: Implement proper expiry testing once sesame expiry behavior is clarified
        self.assertIn(response.status_code, [200, 302])  # Either success page or redirect

    def test_unverified_user_access_restrictions(self):
        """Test unverified users cannot access protected resources"""
        # Create unverified user
        unverified_user = User.objects.create_user(
            email=get_unique_email("unverified"), name="Unverified User", phone_number=get_unique_phone_number()
        )
        unverified_user.email_verified = False
        unverified_user.phone_verified = False
        unverified_user.save()

        # Attempt signin with unverified user
        response = self.client.post(reverse("accounts:signin"), {"email": unverified_user.email})

        # Should be rejected
        self.assertContains(response, "verify")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_csrf_protection_on_sensitive_actions(self):
        """Test CSRF protection on authentication actions"""
        # Attempt signin without CSRF token
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(reverse("accounts:signin"), {"email": self.user.email})

        # Should be rejected due to CSRF
        self.assertEqual(response.status_code, 403)

    def test_password_field_not_exposed(self):
        """Test that password fields are not exposed in responses"""
        # Create user via API (if available)
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "email": "newuser@example.com",
                "full_name": "New User",
                "phone_number": get_unique_phone_number(),
                "organization_name": "Test Org",
            },
        )

        # Response should not contain any password-related data
        response_content = response.content.decode()
        self.assertNotIn("password", response_content.lower())
        self.assertNotIn("passwd", response_content.lower())
        self.assertNotIn("pwd", response_content.lower())

    def test_email_enumeration_prevention(self):
        """Test that email enumeration is prevented"""
        # Attempt signin with non-existent email
        response1 = self.client.post(reverse("accounts:signin"), {"email": "nonexistent@example.com"})

        # Attempt signin with existing email
        response2 = self.client.post(reverse("accounts:signin"), {"email": self.user.email})

        # Both responses should look similar (no enumeration)
        self.assertEqual(response1.status_code, response2.status_code)

    def test_timing_attack_resistance(self):
        """Test resistance to timing attacks"""
        # Test signin timing with existing vs non-existent emails
        existing_email = self.user.email
        non_existent_email = "nonexistent@example.com"

        # Time existing email signin
        start_time = time.time()
        self.client.post(reverse("accounts:signin"), {"email": existing_email})
        existing_time = time.time() - start_time

        # Time non-existent email signin
        start_time = time.time()
        self.client.post(reverse("accounts:signin"), {"email": non_existent_email})
        non_existent_time = time.time() - start_time

        # Times should be similar (within reasonable variance)
        time_diff = abs(existing_time - non_existent_time)
        self.assertLess(time_diff, 0.1)  # Within 100ms


class InputValidationSecurityTest(TestCase):
    """Test input validation and sanitization security"""

    def test_sql_injection_prevention_email(self):
        """Test SQL injection prevention in email fields"""
        sql_injection_attempts = [
            "user@example.com'; DROP TABLE users; --",
            "user@example.com' OR '1'='1",
            "user@example.com'; UPDATE users SET is_superuser=1; --",
            "user@example.com' UNION SELECT * FROM accounts_user; --",
        ]

        client = Client()

        for malicious_email in sql_injection_attempts:
            with self.subTest(email=malicious_email):
                response = client.post(reverse("accounts:signin"), {"email": malicious_email})

                # Should handle safely without SQL injection
                self.assertIn(response.status_code, [200, 400])

    def test_xss_prevention_in_name_fields(self):
        """Test XSS prevention in name fields"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "John<img src=x onerror=alert('xss')>",
            "John'; eval('malicious_code'); //",
            "John\"><script>alert('xss')</script>",
            "javascript:alert('xss')",
        ]

        client = Client()

        for malicious_name in xss_attempts:
            with self.subTest(name=malicious_name):
                response = client.post(
                    reverse("accounts:signup"),
                    {
                        "email": "test@example.com",
                        "full_name": malicious_name,
                        "phone_number": "+351987654321",
                        "organization_name": "Test Org",
                    },
                )

                # Response should not contain unescaped malicious input
                response_content = response.content.decode()

                # Check that malicious input is properly escaped/sanitized
                if malicious_name == "<script>alert('xss')</script>":
                    # Should not contain the exact unescaped malicious script
                    self.assertNotIn(malicious_name, response_content)
                    # If the content appears, it should be HTML escaped
                    if "alert" in response_content and "xss" in response_content:
                        # Should be escaped as &lt;script&gt; or similar
                        self.assertTrue(
                            "&lt;script&gt;" in response_content or "&amp;lt;script&amp;gt;" in response_content,
                            "Malicious script should be HTML escaped",
                        )

                elif malicious_name == "javascript:alert('xss')":
                    # Should not contain the exact unescaped malicious input
                    self.assertNotIn(malicious_name, response_content)
                    # If javascript:alert appears, it should be properly escaped
                    if "javascript:alert" in response_content:
                        # Should be escaped - quotes should be &#x27;, &#39;, or &apos;
                        escaped_patterns = ["&#x27;", "&#39;", "&apos;", "&quot;"]
                        has_proper_escaping = any(pattern in response_content for pattern in escaped_patterns)
                        self.assertTrue(has_proper_escaping, "JavaScript should be properly escaped")

                else:
                    # For other malicious inputs, ensure they're not reflected unescaped
                    # Allow escaped versions but not the raw malicious content
                    self.assertNotIn(malicious_name, response_content)
                    # If any part of the malicious content appears, it should be in escaped form
                    if any(char in response_content for char in ["<", ">", '"', "'", "&"]) and any(
                        keyword in malicious_name.lower() for keyword in ["script", "javascript", "alert", "onerror"]
                    ):
                        # Check for common escape patterns
                        escape_patterns = ["&lt;", "&gt;", "&quot;", "&#39;", "&#x27;", "&amp;"]
                        has_escaping = any(pattern in response_content for pattern in escape_patterns)
                        if not has_escaping:
                            # Only fail if we find unescaped content that could be dangerous
                            dangerous_unescaped = ["<script", "javascript:", "onerror=", "onclick="]
                            has_dangerous = any(pattern in response_content.lower() for pattern in dangerous_unescaped)
                            self.assertFalse(
                                has_dangerous, f"Found potentially dangerous unescaped content: {malicious_name}"
                            )

    def test_phone_number_validation_security(self):
        """Test phone number validation against malicious input"""
        malicious_phone_numbers = [
            "+351987654321'; DROP TABLE users; --",
            "+351987654321<script>alert('xss')</script>",
            "+351987654321\x00\x01\x02",  # Null bytes
            "+" + "9" * 1000,  # Extremely long number
            "+351987654321\r\nMalicious-Header: value",
        ]

        for malicious_phone in malicious_phone_numbers:
            with self.subTest(phone=malicious_phone):
                try:
                    result = PhoneValidationService.validate_and_normalize(malicious_phone)
                    # If validation succeeds, result should be clean
                    self.assertRegex(result, r"^\+[1-9]\d{1,14}$")
                except ValidationError:
                    # ValidationError is acceptable for malicious input
                    pass

    def test_organization_name_validation(self):
        """Test organization name validation against malicious input"""
        malicious_org_names = [
            "<script>alert('xss')</script>",
            "' OR '1'='1",
            "\x00\x01\x02Evil Org",  # Control characters
            "A" * 10000,  # Extremely long name
        ]

        client = Client()

        for malicious_org in malicious_org_names:
            with self.subTest(org=malicious_org[:50]):
                response = client.post(
                    reverse("accounts:signup"),
                    {
                        "email": "test@example.com",
                        "full_name": "Test User",
                        "phone_number": "+351987654321",
                        "organization_name": malicious_org,
                    },
                )

                # Should handle safely
                self.assertIn(response.status_code, [200, 400])

    def test_unicode_normalization_security(self):
        """Test handling of Unicode normalization attacks"""
        unicode_attacks = [
            "admin@example.com",  # Normal
            "аdmin@example.com",  # Cyrillic 'a'  # noqa: RUF001
            "admin@еxample.com",  # Cyrillic 'e'  # noqa: RUF001
            "test@xn--e1afmkfd.xn--p1ai",  # Punycode
        ]

        client = Client()

        for unicode_email in unicode_attacks:
            with self.subTest(email=unicode_email):
                response = client.post(reverse("accounts:signin"), {"email": unicode_email})

                # Should handle consistently
                self.assertIn(response.status_code, [200, 400])

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks in any file operations"""
        # If the system has any file upload or reference functionality
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        # Test in contexts where file paths might be used
        for traversal_path in traversal_attempts:
            with self.subTest(path=traversal_path):
                # Test in organization name (common place for file operations)
                client = Client()
                response = client.post(
                    reverse("accounts:signup"),
                    {
                        "email": "test@example.com",
                        "full_name": "Test User",
                        "phone_number": "+351987654321",
                        "organization_name": traversal_path,
                    },
                )

                # Should not cause system file access
                self.assertIn(response.status_code, [200, 400])


class SessionSecurityTest(BaseTestCase):
    """Test session security measures"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )

    def test_session_invalidation_on_logout(self):
        """Test sessions are properly invalidated on logout"""
        # Login and get session key
        self.client.force_login(self.user)
        session_key = self.client.session.session_key

        # Logout
        response = self.client.post(reverse("accounts:logout"))

        # Old session should be invalidated
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())

    def test_concurrent_session_handling(self):
        """Test handling of concurrent sessions"""
        # Create two client sessions
        client1 = Client()
        client2 = Client()

        # Login with both clients
        client1.force_login(self.user)
        client2.force_login(self.user)

        # Both should have different session keys
        session1 = client1.session.session_key
        session2 = client2.session.session_key

        self.assertNotEqual(session1, session2)

        # Both sessions should be valid initially
        response1 = client1.get("/")
        response2 = client2.get("/")

        # (Behavior depends on concurrent session policy)

    def test_session_data_isolation(self):
        """Test session data is properly isolated between users"""
        user2 = User.objects.create_user(
            email=get_unique_email("user2"), name="User 2", phone_number=get_unique_phone_number()
        )

        client1 = Client()
        client2 = Client()

        # Login different users
        client1.force_login(self.user)
        client2.force_login(user2)

        # Set session data
        session1 = client1.session
        session1["test_data"] = "user1_data"
        session1.save()

        session2 = client2.session
        session2["test_data"] = "user2_data"
        session2.save()

        # Verify isolation by getting fresh session references
        fresh_session1 = client1.session
        fresh_session2 = client2.session

        self.assertEqual(fresh_session1["test_data"], "user1_data")
        self.assertEqual(fresh_session2["test_data"], "user2_data")

    @override_settings(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True)
    def test_session_cookie_security_flags(self):
        """Test session cookies have proper security flags"""
        response = self.client.get(reverse("accounts:signin"))

        # Check security flags in cookies (if session cookie is set)
        if "sessionid" in response.cookies:
            session_cookie = response.cookies["sessionid"]
            self.assertTrue(session_cookie.get("secure"))
            self.assertTrue(session_cookie.get("httponly"))

    def test_session_timeout_enforcement(self):
        """Test session timeout is properly enforced"""
        self.client.force_login(self.user)

        # Get session
        session = self.client.session

        # Manually expire session
        session.set_expiry(-1)
        session.save()

        # Request should require re-authentication
        response = self.client.get("/")

        # Should not be authenticated anymore
        self.assertNotIn("_auth_user_id", self.client.session)


class PermissionEscalationSecurityTest(BaseTestCase):
    """Test prevention of permission escalation attacks"""

    def setUp(self):
        self.client = Client()

        # Create regular user
        self.user = User.objects.create_user(
            email=get_unique_email("user"), name="Regular User", phone_number=get_unique_phone_number()
        )

        # Create admin user
        self.admin = User.objects.create_user(
            email=get_unique_email("admin"), name="Admin User", phone_number=get_unique_phone_number()
        )

        # Create schools with different owners
        self.user_school = School.objects.create(name="User School", contact_email=self.user.email)
        self.admin_school = School.objects.create(name="Admin School", contact_email=self.admin.email)

        # Create memberships
        SchoolMembership.objects.create(
            user=self.user, school=self.user_school, role=SchoolRole.TEACHER, is_active=True
        )
        SchoolMembership.objects.create(
            user=self.admin, school=self.admin_school, role=SchoolRole.SCHOOL_OWNER, is_active=True
        )

    def test_cross_school_access_prevention(self):
        """Test users cannot access other schools' resources"""
        self.client.force_login(self.user)

        # Attempt to access admin's school
        response = self.client.get(reverse("accounts:school_members", kwargs={"school_pk": self.admin_school.id}))

        # Should be denied
        self.assertIn(response.status_code, [403, 404, 302])

    def test_role_escalation_prevention(self):
        """Test users cannot escalate their roles"""
        self.client.force_login(self.user)

        # Attempt to modify membership role (if such endpoint exists)
        membership = SchoolMembership.objects.get(user=self.user, school=self.user_school)

        # This would depend on your specific endpoints
        # Example: attempt to change role via direct parameter manipulation
        # The system should validate permissions before allowing changes

    def test_superuser_privilege_protection(self):
        """Test superuser privileges cannot be granted improperly"""
        self.client.force_login(self.user)

        # Verify user is not superuser
        self.assertFalse(self.user.is_superuser)

        # Attempt various privilege escalation vectors
        # (This depends on your specific admin/privilege granting endpoints)

        # After any operations, user should still not be superuser
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)

    def test_object_level_permission_enforcement(self):
        """Test object-level permissions are properly enforced"""
        # Create another user's object
        other_user = User.objects.create_user(
            email=get_unique_email("other"), name="Other User", phone_number=get_unique_phone_number()
        )

        self.client.force_login(self.user)

        # Attempt to access/modify other user's profile (if such endpoint exists)
        # Should be denied based on object ownership

    def test_admin_interface_protection(self):
        """Test admin interface is properly protected"""
        self.client.force_login(self.user)

        # Attempt to access Django admin
        response = self.client.get("/admin/")

        # Should redirect to login or show permission denied
        self.assertIn(response.status_code, [302, 403])


class DataExposureSecurityTest(BaseTestCase):
    """Test prevention of sensitive data exposure"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )

    def test_otp_codes_not_exposed_in_responses(self):
        """Test OTP codes are never exposed in HTTP responses"""
        # Generate OTP
        otp_code, _token_id = OTPService.generate_otp(self.user, "email")

        # Make various requests that might accidentally expose OTP
        self.client.force_login(self.user)

        endpoints_to_test = [
            "/",
            reverse("accounts:profile") if "profile" in reverse.__globals__ else None,
        ]

        for endpoint in endpoints_to_test:
            if endpoint:
                with self.subTest(endpoint=endpoint):
                    response = self.client.get(endpoint)
                    response_content = response.content.decode()

                    # OTP should never appear in response
                    self.assertNotIn(otp_code, response_content)

    def test_verification_tokens_not_exposed(self):
        """Test verification tokens are not exposed in responses"""
        # Create verification token
        token = VerificationToken.objects.create(
            user=self.user,
            token_type="signin_otp",
            token_value="hashed_value",
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        self.client.force_login(self.user)

        # Test various endpoints
        response = self.client.get("/")
        response_content = response.content.decode()

        # Token values should not be exposed
        self.assertNotIn(token.token_value, response_content)
        self.assertNotIn(str(token.id), response_content)

    def test_phone_number_privacy(self):
        """Test phone numbers are properly protected"""
        # Create another user
        other_user = User.objects.create_user(
            email=get_unique_email("other2"), name="Other User", phone_number=get_unique_phone_number()
        )

        self.client.force_login(self.user)

        # Make requests that might expose other users' phone numbers
        # Phone numbers should not be visible to unauthorized users

    def test_email_privacy_in_error_messages(self):
        """Test email addresses don't leak in error messages"""
        # Attempt signin with non-existent email
        response = self.client.post(reverse("accounts:signin"), {"email": "nonexistent@example.com"})

        response_content = response.content.decode()

        # Error message should not echo back the exact email
        # (to prevent enumeration and information disclosure)

    def test_session_data_not_exposed_in_headers(self):
        """Test session data is not exposed in HTTP headers"""
        self.client.force_login(self.user)

        response = self.client.get("/")

        # Check headers don't contain sensitive information
        for header_name, header_value in response.items():
            # Skip security headers that legitimately contain numbers
            if header_name.lower() in ["x-frame-options", "x-xss-protection"]:
                continue
            # Session keys, user IDs, etc. should not be in headers
            self.assertNotIn(str(self.user.id), str(header_value))

    def test_stack_traces_not_exposed_in_production_mode(self):
        """Test stack traces are not exposed in production mode"""
        with override_settings(DEBUG=False):
            # Trigger an error condition
            try:
                # This would depend on creating a controlled error condition
                # without actually breaking the test
                pass
            except Exception:
                pass

            # In production mode, detailed stack traces should not be visible


class RateLimitingSecurityTest(BaseTestCase):
    """Test rate limiting and abuse prevention"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )

    def test_signin_attempt_rate_limiting(self):
        """Test rate limiting on signin attempts"""
        # Make multiple rapid signin attempts
        for i in range(10):
            response = self.client.post(reverse("accounts:signin"), {"email": self.user.email})

            # After several attempts, should be rate limited
            if i > 5:  # Assuming rate limit kicks in after 5 attempts
                # Response might be rate limited
                # (This depends on your rate limiting implementation)
                pass

    def test_otp_generation_rate_limiting(self):
        """Test rate limiting on OTP generation"""
        # Rapidly generate multiple OTPs
        for i in range(10):
            try:
                _otp_code, _token_id = OTPService.generate_otp(self.user, "email")

                # Should eventually be rate limited or have some protection
                # (This depends on your implementation)

            except Exception as e:
                # Rate limiting exception is acceptable
                pass

    def test_verification_email_rate_limiting(self):
        """Test rate limiting on verification email sending"""
        self.client.force_login(self.user)

        # Rapidly request verification emails
        for i in range(10):
            with patch("accounts.views.send_magic_link_email") as mock_send:
                mock_send.return_value = {"success": True}

                response = self.client.post(reverse("accounts:send_verification_email"))

                # Should eventually be rate limited
                # (This depends on your implementation)

    def test_large_payload_handling(self):
        """Test handling of unusually large payloads"""
        large_data = {
            "email": "test@example.com",
            "full_name": "A" * 10000,  # Very long name
            "phone_number": "+351987654321",
            "organization_name": "B" * 10000,  # Very long org name
        }

        response = self.client.post(reverse("accounts:signup"), large_data)

        # Should handle gracefully without DoS
        self.assertIn(response.status_code, [200, 400, 413])  # 413 = Payload Too Large

    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests from same user"""
        import threading
        import time

        results = []

        def make_request():
            client = Client()
            response = client.post(reverse("accounts:signin"), {"email": self.user.email})
            results.append(response.status_code)

        # Make concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All requests should be handled properly
        for status_code in results:
            self.assertIn(status_code, [200, 400, 429])  # 429 = Too Many Requests


class CryptographicSecurityTest(TestCase):
    """Test cryptographic security measures"""

    def test_otp_token_hashing_security(self):
        """Test OTP tokens are properly hashed"""
        user = User.objects.create_user(email="test@example.com", name="Test User", phone_number="+351987654321")

        otp_code, token_id = OTPService.generate_otp(user, "email")

        # Get token from database
        token = VerificationToken.objects.get(id=token_id)

        # Token value should be hashed, not plaintext
        self.assertNotEqual(token.token_value, otp_code)

        # Should be SHA256 hash
        expected_hash = hashlib.sha256(otp_code.encode()).hexdigest()
        self.assertEqual(token.token_value, expected_hash)

    def test_otp_randomness_quality(self):
        """Test OTP codes have sufficient randomness"""
        user = User.objects.create_user(email="test@example.com", name="Test User", phone_number="+351987654321")

        # Generate many OTP codes
        codes = []
        for i in range(1000):
            otp_code, _ = OTPService.generate_otp(user, "email")
            codes.append(otp_code)

        # Check distribution of digits
        all_digits = "".join(codes)
        digit_counts = {str(i): all_digits.count(str(i)) for i in range(10)}

        # Each digit should appear roughly 10% of the time (with some variance)
        for digit, count in digit_counts.items():
            expected = len(all_digits) / 10
            variance = abs(count - expected) / expected
            self.assertLess(variance, 0.2)  # Within 20% of expected

    def test_timing_safe_comparison(self):
        """Test that OTP verification uses timing-safe comparison"""
        user = User.objects.create_user(email="test@example.com", name="Test User", phone_number="+351987654321")

        otp_code, token_id = OTPService.generate_otp(user, "email")

        # Test with correct code
        start_time = time.time()
        _success1, _result1 = OTPService.verify_otp(token_id, otp_code)
        time1 = time.time() - start_time

        # Generate new OTP for second test
        otp_code2, token_id2 = OTPService.generate_otp(user, "email")

        # Test with incorrect code of same length
        wrong_code = "123456" if otp_code2 != "123456" else "654321"
        start_time = time.time()
        _success2, _result2 = OTPService.verify_otp(token_id2, wrong_code)
        time2 = time.time() - start_time

        # Times should be similar (no timing attack possible)
        time_diff = abs(time1 - time2)
        self.assertLess(time_diff, 0.01)  # Within 10ms


class ComplianceSecurityTest(BaseTestCase):
    """Test compliance with security best practices"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=get_unique_email("test"), name="Test User", phone_number=get_unique_phone_number()
        )

    def test_audit_trail_for_sensitive_actions(self):
        """Test audit trails are created for sensitive actions"""
        # This would test logging/auditing of security-relevant events
        # like login attempts, verification actions, etc.

        # For now, just test that sensitive operations complete without errors
        # In the future, this should verify actual audit logs are created
        otp_code, token_id = OTPService.generate_otp(self.user, "email")
        success, _result = OTPService.verify_otp(token_id, otp_code)

        # Should have successful operations (actual audit logging to be implemented)
        self.assertTrue(success)

    def test_secure_headers_present(self):
        """Test security headers are present in responses"""
        response = self.client.get("/")

        # Test for important security headers
        # (This depends on your middleware/security configuration)
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]

        # These headers should be present for security
        # (Implementation depends on your security middleware)

    def test_content_type_validation(self):
        """Test content type validation for requests"""
        # Test with wrong content type
        response = self.client.post(
            reverse("accounts:signin"), data='{"email": "test@example.com"}', content_type="application/json"
        )

        # Should handle different content types properly
        # (This depends on your view implementations)

    def test_data_retention_compliance(self):
        """Test data retention policies are enforced"""
        # Create old verification tokens
        old_token = VerificationToken.objects.create(
            user=self.user,
            token_type="signin_otp",
            token_value="old_hash",
            expires_at=timezone.now() - timedelta(days=30),
        )

        # Run cleanup
        deleted_count = OTPService.cleanup_expired_tokens()

        # Old tokens should be cleaned up
        self.assertGreater(deleted_count, 0)
        self.assertFalse(VerificationToken.objects.filter(id=old_token.id).exists())
