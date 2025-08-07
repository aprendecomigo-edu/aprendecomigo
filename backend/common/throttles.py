from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


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
        
        # Handle case where student_info might be a string or other type
        if isinstance(student_info, dict):
            email = student_info.get("email", "")
        elif isinstance(student_info, str):
            # If student_info is a string, try to use it as email if it looks like one
            email = student_info if "@" in student_info else ""
        else:
            # For any other type, fallback to empty string
            email = ""
            
        if not email:
            # Fallback to IP-based if no email provided
            return None
        return self.cache_format % {"scope": self.scope, "ident": email.lower()}


class BulkInvitationThrottle(UserRateThrottle):
    """Rate limit for bulk teacher invitations - based on authenticated user"""
    
    rate = "100/h"  # 100 invitations per hour per user (reasonable for school admins)
    scope = "bulk_invitations"


class BulkInvitationIPThrottle(AnonRateThrottle):
    """Rate limit for bulk teacher invitations - based on IP address (backup protection)"""
    
    rate = "200/h"  # 200 invitations per hour per IP (allows multiple users from same network)
    scope = "bulk_invitations_ip"


class IndividualInvitationThrottle(UserRateThrottle):
    """Rate limit for individual teacher invitations - based on authenticated user"""
    
    rate = "50/h"  # 50 individual invitations per hour per user
    scope = "individual_invitations"
