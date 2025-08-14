"""
Secure cache key utilities.

Provides secure cache key generation with hash-based keys to prevent
cache poisoning attacks.
"""

import hashlib
import json
import time
from typing import Any

from django.contrib.auth import get_user_model

User = get_user_model()


class SecureCacheKeyGenerator:
    """
    Secure cache key generator that uses hash-based keys to prevent
    cache poisoning attacks.
    """

    @staticmethod
    def generate_user_scoped_key(
        prefix: str, user_id: int, params: dict[str, Any], session_token: str | None = None
    ) -> str:
        """
        Generate a secure cache key scoped to a specific user.

        Args:
            prefix: Cache key prefix (e.g., 'tutor_analytics')
            user_id: User ID for scoping
            params: Dictionary of parameters to include in key
            session_token: Optional session token for additional security

        Returns:
            Secure hash-based cache key
        """
        # Build key components
        key_data = {"prefix": prefix, "user_id": user_id, "params": params}

        # Add session token if provided for additional security
        if session_token:
            key_data["session_token"] = session_token

        # Create deterministic hash
        key_string = json.dumps(key_data, sort_keys=True, separators=(",", ":"))
        key_hash = hashlib.sha256(key_string.encode("utf-8")).hexdigest()[:16]

        # Return prefixed hash key
        return f"secure_{prefix}_{key_hash}"

    @staticmethod
    def generate_school_metrics_key(school_id: int, session_token: str | None = None) -> str:
        """
        Generate secure school metrics cache key.

        Args:
            school_id: School ID
            session_token: Optional session token

        Returns:
            Secure school metrics cache key
        """
        params = {"timestamp": str(int(time.time() // 300))}  # 5-minute buckets

        return SecureCacheKeyGenerator.generate_user_scoped_key("school_metrics", school_id, params, session_token)

    @staticmethod
    def generate_discovery_key(
        filters: dict[str, Any], pagination: dict[str, Any], ordering: str, session_token: str | None = None
    ) -> str:
        """
        Generate secure tutor discovery cache key.

        Args:
            filters: Search filters
            pagination: Pagination parameters
            ordering: Ordering parameter
            session_token: Optional session token

        Returns:
            Secure discovery cache key
        """
        params = {"filters": filters, "pagination": pagination, "ordering": ordering}

        # Use 0 as user_id for public discovery endpoint
        return SecureCacheKeyGenerator.generate_user_scoped_key("tutor_discovery", 0, params, session_token)

    @staticmethod
    def get_session_token_from_request(request) -> str | None:
        """
        Extract session token from request for cache key generation.

        Args:
            request: Django request object

        Returns:
            Session token if available, None otherwise
        """
        if hasattr(request, "user") and request.user.is_authenticated:
            # Use a portion of the user's session key if available
            session_key = getattr(request.session, "session_key", None)
            if session_key:
                # Use first 8 characters of session key for cache scoping
                return session_key[:8]
        return None


def invalidate_user_cache_pattern(prefix: str, user_id: int):
    """
    Invalidate all cache entries matching a user-scoped pattern.

    Note: This is a simple implementation. For production, consider
    using cache tagging or a more sophisticated cache invalidation strategy.

    Args:
        prefix: Cache key prefix
        user_id: User ID to invalidate cache for
    """
    # This is a simplified invalidation - in production you might want
    # to use cache tagging or maintain a registry of cache keys
    cache_pattern = f"secure_{prefix}_{user_id}_*"

    # Note: Django's cache doesn't support pattern-based deletion by default
    # This would need to be implemented based on the cache backend
    # For now, we'll just note that this pattern should be used
    pass
