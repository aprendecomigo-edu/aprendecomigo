"""
Rate limiting utilities for Stripe API calls.

This module provides rate limiting functionality to prevent exceeding Stripe API quotas
and ensures smooth operation of payment processing services.
"""

from datetime import datetime
from functools import wraps
import logging
import time
from typing import Any

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class StripeRateLimiter:
    """
    Rate limiter for Stripe API calls to prevent quota exhaustion.

    This class implements a token bucket algorithm with Redis-backed storage
    for distributed rate limiting across multiple application instances.
    """

    # Stripe API rate limits (as of 2025)
    # Read operations: 100 requests per second
    # Write operations: 100 requests per second
    # These are conservative limits to ensure we stay well under Stripe's thresholds
    DEFAULT_LIMITS = {
        "read_operations": {
            "requests_per_second": 80,  # Conservative limit
            "burst_allowance": 10,
        },
        "write_operations": {
            "requests_per_second": 50,  # More conservative for writes
            "burst_allowance": 5,
        },
    }

    def __init__(self, cache_prefix: str = "stripe_rate_limit"):
        """
        Initialize rate limiter.

        Args:
            cache_prefix: Prefix for cache keys
        """
        self.cache_prefix = cache_prefix
        self.limits = getattr(settings, "STRIPE_RATE_LIMITS", self.DEFAULT_LIMITS)

    def is_allowed(self, operation_type: str, identifier: str = "default") -> dict[str, Any]:
        """
        Check if a request is allowed under rate limiting rules.

        Args:
            operation_type: Type of operation ('read_operations' or 'write_operations')
            identifier: Unique identifier for the rate limit (e.g., user_id, service_name)

        Returns:
            Dict containing allowed status and rate limit info
        """
        if operation_type not in self.limits:
            logger.warning(f"Unknown operation type: {operation_type}")
            return {"allowed": True, "reason": "unknown_operation_type"}

        limit_config = self.limits[operation_type]
        requests_per_second = limit_config["requests_per_second"]
        burst_allowance = limit_config["burst_allowance"]

        # Create cache key
        cache_key = f"{self.cache_prefix}:{operation_type}:{identifier}"
        current_time = time.time()

        # Get current state from cache
        rate_limit_data = cache.get(
            cache_key,
            {
                "tokens": requests_per_second + burst_allowance,  # Start with full bucket
                "last_refill": current_time,
                "requests_made": 0,
            },
        )

        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - rate_limit_data["last_refill"]
        tokens_to_add = time_elapsed * requests_per_second

        # Update token count (token bucket algorithm)
        max_tokens = requests_per_second + burst_allowance
        new_token_count = min(max_tokens, rate_limit_data["tokens"] + tokens_to_add)

        # Check if request is allowed
        if new_token_count >= 1:
            # Allow request and consume token
            rate_limit_data.update(
                {
                    "tokens": new_token_count - 1,
                    "last_refill": current_time,
                    "requests_made": rate_limit_data["requests_made"] + 1,
                }
            )

            # Store updated state in cache (expire after 1 hour)
            cache.set(cache_key, rate_limit_data, timeout=3600)

            return {
                "allowed": True,
                "tokens_remaining": rate_limit_data["tokens"],
                "requests_made": rate_limit_data["requests_made"],
                "reset_time": current_time + (max_tokens / requests_per_second),
            }
        else:
            # Rate limit exceeded
            reset_time = current_time + (1 / requests_per_second)
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "tokens_remaining": 0,
                "retry_after": reset_time - current_time,
                "reset_time": reset_time,
            }

    def wait_if_needed(self, operation_type: str, identifier: str = "default") -> None:
        """
        Wait if rate limit would be exceeded, ensuring request succeeds.

        Args:
            operation_type: Type of operation
            identifier: Unique identifier for the rate limit
        """
        check_result = self.is_allowed(operation_type, identifier)

        if not check_result["allowed"]:
            wait_time = check_result.get("retry_after", 1)
            logger.info(f"Rate limit exceeded for {operation_type}. Waiting {wait_time:.2f} seconds.")
            time.sleep(wait_time)

    def get_rate_limit_status(self, operation_type: str, identifier: str = "default") -> dict[str, Any]:
        """
        Get current rate limit status without consuming a token.

        Args:
            operation_type: Type of operation
            identifier: Unique identifier for the rate limit

        Returns:
            Dict containing current rate limit status
        """
        cache_key = f"{self.cache_prefix}:{operation_type}:{identifier}"
        current_time = time.time()

        rate_limit_data = cache.get(
            cache_key,
            {
                "tokens": self.limits[operation_type]["requests_per_second"],
                "last_refill": current_time,
                "requests_made": 0,
            },
        )

        limit_config = self.limits[operation_type]
        requests_per_second = limit_config["requests_per_second"]
        burst_allowance = limit_config["burst_allowance"]
        max_tokens = requests_per_second + burst_allowance

        # Calculate current tokens
        time_elapsed = current_time - rate_limit_data["last_refill"]
        tokens_to_add = time_elapsed * requests_per_second
        current_tokens = min(max_tokens, rate_limit_data["tokens"] + tokens_to_add)

        return {
            "operation_type": operation_type,
            "requests_per_second_limit": requests_per_second,
            "burst_allowance": burst_allowance,
            "current_tokens": current_tokens,
            "max_tokens": max_tokens,
            "requests_made": rate_limit_data["requests_made"],
            "last_refill": rate_limit_data["last_refill"],
        }


# Global rate limiter instance
stripe_rate_limiter = StripeRateLimiter()


def stripe_rate_limit(operation_type: str = "write_operations", identifier: str | None = None):
    """
    Decorator to apply rate limiting to Stripe API calls.

    Args:
        operation_type: Type of operation ('read_operations' or 'write_operations')
        identifier: Optional identifier for rate limiting (defaults to function name)

    Usage:
        @stripe_rate_limit('read_operations')
        def get_payment_intent(payment_intent_id):
            return stripe.PaymentIntent.retrieve(payment_intent_id)

        @stripe_rate_limit('write_operations', 'refund_service')
        def create_refund(payment_intent_id, amount):
            return stripe.Refund.create(payment_intent=payment_intent_id, amount=amount)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as identifier if not provided
            rate_limit_id = identifier or f"{func.__module__}.{func.__name__}"

            # Check rate limit and wait if needed
            stripe_rate_limiter.wait_if_needed(operation_type, rate_limit_id)

            # Execute the function
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Log the error but don't modify rate limiting behavior
                logger.error(f"Error in rate-limited function {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


def get_stripe_rate_limit_stats() -> dict[str, Any]:
    """
    Get comprehensive rate limiting statistics for monitoring.

    Returns:
        Dict containing rate limiting statistics
    """
    stats = {
        "read_operations": stripe_rate_limiter.get_rate_limit_status("read_operations"),
        "write_operations": stripe_rate_limiter.get_rate_limit_status("write_operations"),
        "timestamp": datetime.now().isoformat(),
    }

    return stats


def reset_stripe_rate_limits(identifier: str = "default") -> dict[str, Any]:
    """
    Reset rate limits for a specific identifier (admin function).

    Args:
        identifier: Identifier to reset rate limits for

    Returns:
        Dict containing reset results
    """
    cache_prefix = stripe_rate_limiter.cache_prefix
    reset_count = 0

    for operation_type in stripe_rate_limiter.limits:
        cache_key = f"{cache_prefix}:{operation_type}:{identifier}"
        if cache.delete(cache_key):
            reset_count += 1

    logger.info(f"Reset {reset_count} rate limit entries for identifier: {identifier}")

    return {
        "success": True,
        "reset_count": reset_count,
        "identifier": identifier,
        "timestamp": datetime.now().isoformat(),
    }
