from rest_framework.throttling import AnonRateThrottle


class EmailCodeRequestThrottle(AnonRateThrottle):
    """Rate limit for email verification code requests - based on email address"""

    rate = "3/5m"  # 3 requests per 5 minutes
    scope = "auth_code_request"

    def get_cache_key(self, request, _view):
        email = request.data.get("email", "")
        return self.cache_format % {"scope": self.scope, "ident": email}


class IPSignupThrottle(AnonRateThrottle):
    """Rate limit for signups based on IP address"""

    rate = "3/5m"  # 3 requests per 5 minutes
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
