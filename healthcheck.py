"""
Health check views for Railway deployment.
"""
import logging
import time
import os
from urllib.parse import urlparse

from django.core.cache import cache, caches
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def _is_railway_environment():
    """Check if we're running in Railway environment."""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None


def _test_redis_connection_with_retry(cache_instance, cache_name, max_retries=3, retry_delay=1):
    """Test Redis connection with retry logic for Railway deployment timing issues."""
    import time
    
    for attempt in range(max_retries):
        try:
            test_key = f"health_check_test_{cache_name}_{int(time.time())}"
            test_value = f"test_value_{attempt}_{int(time.time())}"
            
            # Test write
            cache_instance.set(test_key, test_value, timeout=30)
            
            # Test read
            retrieved_value = cache_instance.get(test_key)
            
            if retrieved_value == test_value:
                # Cleanup
                cache_instance.delete(test_key)
                return {"success": True, "attempt": attempt + 1}
            else:
                raise Exception(f"Cache read/write mismatch. Expected: {test_value}, Got: {retrieved_value}")
                
        except Exception as e:
            logger.warning(f"Redis {cache_name} connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                return {"success": False, "error": str(e), "attempts": max_retries}
    
    return {"success": False, "error": "Max retries exceeded", "attempts": max_retries}


@never_cache
@csrf_exempt
def health_detailed(request):
    """
    Detailed health check that validates all critical dependencies.
    For Railway deployments:
    - Database connectivity is REQUIRED
    - Redis connectivity is REQUIRED for production but can be degraded during initial deployment
    - Health check will fail if core dependencies are not available after retry attempts
    """
    logger.info("Starting health check")
    
    try:
        health_data = {
            "status": "ok",
            "timestamp": time.time(),
            "environment": "railway" if _is_railway_environment() else "local",
            "checks": {}
        }

        overall_healthy = True
        is_railway = _is_railway_environment()

        # 1. Database connectivity check
        try:
            logger.info("Checking database connectivity")
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    health_data["checks"]["database"] = {
                        "status": "healthy",
                        "details": "PostgreSQL connection successful"
                    }
                    logger.info("Database check passed")
                else:
                    raise Exception("Unexpected query result")
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False

        # 2. Default cache (Redis) connectivity check
        logger.info("Checking Redis default cache with retry logic")
        redis_default_result = _test_redis_connection_with_retry(cache, "default", max_retries=3 if is_railway else 1)
        
        if redis_default_result["success"]:
            health_data["checks"]["redis_default"] = {
                "status": "healthy",
                "details": f"Redis default cache operational (attempt {redis_default_result['attempt']})"
            }
            logger.info("Redis default cache check passed")
        else:
            logger.error("Redis default cache failed after retries: %s", redis_default_result["error"])
            health_data["checks"]["redis_default"] = {
                "status": "unhealthy",
                "error": redis_default_result["error"],
                "attempts": redis_default_result.get("attempts", 0)
            }
            
            # For Railway deployments, Redis is critical - fail the health check
            if is_railway:
                overall_healthy = False
                logger.error("Redis default cache is required for Railway deployment - marking health check as failed")
            else:
                # For local development, Redis failures can be tolerated
                logger.warning("Redis default cache failed in local environment - continuing")

        # 3. Sessions cache check with retry logic
        logger.info("Checking Redis sessions cache with retry logic")
        try:
            sessions_cache = caches['sessions']
            redis_sessions_result = _test_redis_connection_with_retry(sessions_cache, "sessions", max_retries=3 if is_railway else 1)
            
            if redis_sessions_result["success"]:
                health_data["checks"]["redis_sessions"] = {
                    "status": "healthy",
                    "details": f"Redis sessions cache operational (attempt {redis_sessions_result['attempt']})"
                }
                logger.info("Redis sessions cache check passed")
            else:
                logger.error("Redis sessions cache failed after retries: %s", redis_sessions_result["error"])
                health_data["checks"]["redis_sessions"] = {
                    "status": "unhealthy",
                    "error": redis_sessions_result["error"],
                    "attempts": redis_sessions_result.get("attempts", 0)
                }
                
                # Sessions are critical for the application
                if is_railway:
                    overall_healthy = False
                    logger.error("Redis sessions cache is required for Railway deployment - marking health check as failed")
                else:
                    logger.warning("Redis sessions cache failed in local environment - continuing")
                    
        except Exception as e:
            logger.error("Failed to access sessions cache configuration: %s", e)
            health_data["checks"]["redis_sessions"] = {
                "status": "unhealthy",
                "error": f"Sessions cache configuration error: {str(e)}"
            }
            overall_healthy = False


        # 4. Railway-specific Redis configuration check
        if is_railway:
            redis_url = os.getenv('REDIS_URL', '')
            parsed_redis = urlparse(redis_url) if redis_url else None
            
            health_data["checks"]["redis_config"] = {
                "redis_url_present": bool(redis_url),
                "redis_host": parsed_redis.hostname if parsed_redis else None,
                "redis_port": parsed_redis.port if parsed_redis else None,
                "is_railway_internal": "railway.internal" in redis_url if redis_url else False
            }
            
            if not redis_url:
                logger.error("REDIS_URL environment variable not set in Railway")
                health_data["checks"]["redis_config"]["status"] = "misconfigured"
                overall_healthy = False
            elif "railway.internal" not in redis_url:
                logger.warning("Redis URL does not use Railway internal network: %s", redis_url)
                health_data["checks"]["redis_config"]["status"] = "suboptimal"
            else:
                health_data["checks"]["redis_config"]["status"] = "configured"

        # Set overall status
        if not overall_healthy:
            health_data["status"] = "unhealthy"
            logger.error("Health check failed - returning 503. Failed checks: %s", 
                        [k for k, v in health_data["checks"].items() 
                         if v.get("status") in ["unhealthy", "misconfigured"]])
            return JsonResponse(health_data, status=503)  # Service Unavailable

        # Check if any services are degraded
        degraded_services = [k for k, v in health_data["checks"].items() 
                           if v.get("status") == "degraded"]
        if degraded_services:
            health_data["status"] = "degraded"
            health_data["degraded_services"] = degraded_services
            logger.warning("Health check passed but some services degraded: %s", degraded_services)
        
        logger.info("Health check passed - returning 200")
        return JsonResponse(health_data, status=200)
        
    except Exception as e:
        logger.error("Health check crashed with exception: %s", e, exc_info=True)
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }, status=500)


@never_cache
@csrf_exempt
def health_simple(request):
    """
    Simple health check for Railway deployment startup phase.
    Only checks database connectivity to allow app to start successfully.
    Redis checks are handled by the detailed health check after startup.
    """
    logger.info("Starting simple health check for Railway startup")
    
    try:
        # Quick database check only
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                logger.info("Simple health check passed - database OK")
                return JsonResponse({
                    "status": "ok",
                    "timestamp": time.time(),
                    "checks": {
                        "database": {"status": "healthy"}
                    }
                }, status=200)
            else:
                raise Exception("Database query returned unexpected result")
                
    except Exception as e:
        logger.error("Simple health check failed: %s", e)
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }, status=503)