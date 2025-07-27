from rest_framework.throttling import AnonRateThrottle


class EmailCodeRequestThrottle(AnonRateThrottle):
    """Rate limit for email verification code requests - based on email address"""

    rate = "5/h"  # 5 requests per hour
    scope = "auth_code_request"

    def get_cache_key(self, request, _view):
        email = request.data.get("email", "")
        return self.cache_format % {"scope": self.scope, "ident": email}


class IPSignupThrottle(AnonRateThrottle):
    """Rate limit for signups based on IP address"""

    rate = "3/h"  # 3 requests per hour
    scope = "auth_signup_ip"


class EmailBasedThrottle(AnonRateThrottle):
    """Rate limit based on email address"""

    rate = "10/h"
    scope = "auth_code_verify_email"

    def get_cache_key(self, request, _view):
        # Get the email from the request data
        email = request.data.get("email", "")
        return self.cache_format % {"scope": self.scope, "ident": email}


class IPBasedThrottle(AnonRateThrottle):
    """Rate limit based on IP address"""

    rate = "30/h"  # Higher limit for IP since it could be shared (e.g., corporate network)
    scope = "auth_code_verify_ip"


class PurchaseInitiationThrottle(AnonRateThrottle):
    """Rate limit for purchase initiation API - based on IP address"""
    
    rate = "10/h"  # 10 purchase attempts per hour per IP
    scope = "purchase_initiation"


class PurchaseInitiationEmailThrottle(AnonRateThrottle):
    """Rate limit for purchase initiation API - based on email address"""
    
    rate = "5/h"  # 5 purchase attempts per hour per email
    scope = "purchase_initiation_email"
    
    def get_cache_key(self, request, _view):
        # Extract email from student_info in the request data
        student_info = request.data.get("student_info", {})
        email = student_info.get("email", "")
        if not email:
            # Fallback to IP-based if no email provided
            return None
        return self.cache_format % {"scope": self.scope, "ident": email.lower()}
