#!/usr/bin/env python3
"""
Wait for Redis to be available before proceeding with application startup.
This script is designed for Railway deployments to handle Redis timing issues.
"""
import os
import sys
import time
import logging
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test Redis connection using the same logic as the health check."""
    try:
        # Import Django components
        import django
        from django.conf import settings
        
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.production')
        django.setup()
        
        from django.core.cache import cache
        
        # Test Redis connection
        test_key = f"startup_test_{int(time.time())}"
        test_value = "startup_ready"
        
        cache.set(test_key, test_value, timeout=30)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            cache.delete(test_key)
            return True
        else:
            logger.warning(f"Redis test failed - expected: {test_value}, got: {retrieved}")
            return False
            
    except Exception as e:
        logger.warning(f"Redis connection test failed: {e}")
        return False

def wait_for_redis(max_wait_time=180, check_interval=5):
    """
    Wait for Redis to become available.
    
    Args:
        max_wait_time (int): Maximum time to wait in seconds (default 3 minutes)
        check_interval (int): Time between checks in seconds (default 5 seconds)
        
    Returns:
        bool: True if Redis is available, False if timeout reached
    """
    redis_url = os.getenv('REDIS_URL', '')
    
    if not redis_url:
        logger.warning("REDIS_URL not set - skipping Redis wait")
        return True
        
    if 'railway.internal' not in redis_url:
        logger.info("Not using Railway internal Redis - skipping wait")
        return True
    
    logger.info(f"Waiting for Redis at {redis_url} (max {max_wait_time}s)")
    
    start_time = time.time()
    attempts = 0
    
    while time.time() - start_time < max_wait_time:
        attempts += 1
        
        logger.info(f"Redis connection attempt {attempts}")
        
        if test_redis_connection():
            elapsed = time.time() - start_time
            logger.info(f"Redis is ready! (took {elapsed:.1f}s, {attempts} attempts)")
            return True
        
        logger.info(f"Redis not ready, waiting {check_interval}s...")
        time.sleep(check_interval)
    
    elapsed = time.time() - start_time
    logger.error(f"Redis not available after {elapsed:.1f}s ({attempts} attempts)")
    return False

if __name__ == "__main__":
    # Parse command line arguments
    max_wait = int(os.getenv('REDIS_WAIT_TIMEOUT', '180'))
    
    logger.info("Starting Redis availability check for Railway deployment")
    
    if wait_for_redis(max_wait_time=max_wait):
        logger.info("Redis is available - proceeding with deployment")
        sys.exit(0)
    else:
        logger.error("Redis is not available - deployment may have issues")
        # Don't fail the deployment, but log the issue
        sys.exit(0)  # Exit with success to allow deployment to continue