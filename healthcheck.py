"""
Health check views for Railway deployment.
"""
import logging
import time

from django.core.cache import cache, caches
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@never_cache
@csrf_exempt
def health_simple(request):
    """
    Simple, fast health check for Railway deployment health monitoring.
    Only checks critical dependencies quickly.
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        # Quick Redis check
        cache.set("health", "ok", timeout=30)
        if cache.get("health") != "ok":
            raise Exception("Redis cache failed")
        cache.delete("health")

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JsonResponse({"status": "error", "error": str(e)}, status=503)


@never_cache
@csrf_exempt
def health_detailed(request):
    """
    Detailed health check that validates all critical dependencies.
    Used for monitoring and debugging.
    """
    logger.info("Starting health check")
    
    try:
        health_data = {
            "status": "ok",
            "timestamp": time.time(),
            "checks": {}
        }

        overall_healthy = True

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
        try:
            logger.info("Checking Redis default cache")
            test_key = "health_check_test"
            test_value = f"test_value_{int(time.time())}"

            # Test write
            cache.set(test_key, test_value, timeout=30)

            # Test read
            retrieved_value = cache.get(test_key)

            if retrieved_value == test_value:
                health_data["checks"]["redis_default"] = {
                    "status": "healthy",
                    "details": "Redis default cache read/write successful"
                }
                logger.info("Redis default cache check passed")
            else:
                raise Exception(f"Cache read/write mismatch. Expected: {test_value}, Got: {retrieved_value}")

            # Cleanup
            cache.delete(test_key)

        except Exception as e:
            logger.error("Redis default cache health check failed: %s", e)
            health_data["checks"]["redis_default"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False

        # 3. Sessions cache check
        try:
            logger.info("Checking Redis sessions cache")
            sessions_cache = caches['sessions']
            test_key = "sessions_health_check_test"
            test_value = f"sessions_test_{int(time.time())}"

            sessions_cache.set(test_key, test_value, timeout=30)
            retrieved_value = sessions_cache.get(test_key)

            if retrieved_value == test_value:
                health_data["checks"]["redis_sessions"] = {
                    "status": "healthy",
                    "details": "Redis sessions cache read/write successful"
                }
                logger.info("Redis sessions cache check passed")
            else:
                raise Exception("Sessions cache read/write mismatch")

            sessions_cache.delete(test_key)

        except Exception as e:
            logger.error("Redis sessions cache health check failed: %s", e)
            health_data["checks"]["redis_sessions"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            overall_healthy = False

        # 4. Template fragments cache check (optional - can degrade gracefully)
        try:
            logger.info("Checking Redis template cache")
            template_cache = caches['template_fragments']
            test_key = "template_health_check_test"
            test_value = f"template_test_{int(time.time())}"

            template_cache.set(test_key, test_value, timeout=30)
            retrieved_value = template_cache.get(test_key)

            if retrieved_value == test_value:
                health_data["checks"]["redis_templates"] = {
                    "status": "healthy",
                    "details": "Redis template cache read/write successful"
                }
                logger.info("Redis template cache check passed")
            else:
                health_data["checks"]["redis_templates"] = {
                    "status": "degraded",
                    "details": "Template cache read/write issues, but non-critical"
                }
                logger.warning("Redis template cache degraded but non-critical")

            template_cache.delete(test_key)

        except Exception as e:
            logger.warning("Redis template cache health check failed (non-critical): %s", e)
            health_data["checks"]["redis_templates"] = {
                "status": "degraded",
                "error": str(e),
                "details": "Template cache issues, but non-critical"
            }
            # Don't mark overall as unhealthy for template cache issues

        # Set overall status
        if not overall_healthy:
            health_data["status"] = "unhealthy"
            logger.error("Health check failed - returning 503: %s", health_data)
            return JsonResponse(health_data, status=503)  # Service Unavailable

        logger.info("Health check passed - returning 200")
        return JsonResponse(health_data, status=200)
        
    except Exception as e:
        logger.error("Health check crashed with exception: %s", e, exc_info=True)
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }, status=500)