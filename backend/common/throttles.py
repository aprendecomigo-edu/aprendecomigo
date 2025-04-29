from rest_framework.throttling import AnonRateThrottle

class EmailCodeRequestThrottle(AnonRateThrottle):
    rate = "5/hour"
    scope = "auth_code_request"


class EmailBasedThrottle(AnonRateThrottle):
    """Rate limit based on email address"""

    rate = "10/hour"
    scope = "auth_code_verify_email"

    def get_cache_key(self, request, view):  # noqa: ARG001
        # Get the email from the request data
        email = request.data.get("email", "")
        return self.cache_format % {"scope": self.scope, "ident": email}


class IPBasedThrottle(AnonRateThrottle):
    """Rate limit based on IP address"""

    rate = "30/hour"  # Higher limit for IP since it could be shared (e.g., corporate network)
    scope = "auth_code_verify_ip"
