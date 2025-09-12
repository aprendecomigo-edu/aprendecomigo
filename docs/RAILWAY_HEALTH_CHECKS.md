# Railway Health Check Strategy

This document outlines the health check implementation designed to handle Redis connectivity issues during Railway deployments.

## Problem Analysis

### Previous Issues
- Railway health checks were failing due to Redis connection refused errors (Error 111)
- Health checks were returning 200 status even when Redis was unavailable
- Redis service timing issues during deployment startup
- Lack of proper retry logic for Railway's internal network delays

### Root Causes Identified
1. **Timing Issues**: Redis service not fully ready during initial health check execution
2. **Network Connectivity**: Railway internal network (`redis.railway.internal`) connection delays
3. **Health Check Logic**: Previous implementation marked Redis failures as "degraded" but still returned 200
4. **Missing Retry Logic**: No retry mechanism for transient connectivity issues

## New Health Check Architecture

### Two-Tier Health Check System

#### 1. Simple Health Check (`/health/`)
- **Purpose**: Railway startup health monitoring
- **Checks**: Database connectivity only  
- **Use Case**: Allows Railway to mark the deployment as "healthy" and route traffic
- **Response**: Fast, minimal dependencies

```python
# Only checks database - allows app to start successfully
def health_simple(request):
    # Quick database check only
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        # Returns 200 if DB is available, 503 if not
```

#### 2. Detailed Health Check (`/health/detailed/`)
- **Purpose**: Comprehensive system monitoring
- **Checks**: Database + Redis with retry logic + Configuration validation
- **Use Case**: Monitoring dashboards, debugging, operational health
- **Response**: Detailed status of all components

### Redis Connection Strategy

#### Retry Logic with Exponential Backoff
```python
def _test_redis_connection_with_retry(cache_instance, cache_name, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Test write/read cycle
            # Success: return immediately
            # Failure: wait with increasing delay
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
```

#### Environment-Specific Behavior
- **Railway Environment**: Redis is required - health check fails if Redis unavailable after retries
- **Local Development**: Redis failures are logged but don't fail health check
- **Configuration Validation**: Checks for proper Railway Redis URL format

### Health Check Response Codes

| Status Code | Condition | Description |
|-------------|-----------|-------------|
| 200 | All systems operational | All critical dependencies working |
| 200 | Systems degraded | Some non-critical services have issues |
| 503 | Unhealthy | Critical dependencies failed (DB, Redis in Railway) |
| 500 | Health check error | Health check itself crashed |

### Railway Configuration

#### Health Check Endpoints
```json
{
  "healthcheckPath": "/health/",
  "healthcheckTimeout": 300
}
```

#### Startup Command Integration
Railway continues to use the existing startup command, but can optionally integrate the Redis wait script:

```bash
# Optional: Wait for Redis before starting
python scripts/wait_for_redis.py && \
python manage.py migrate --noinput && \
python manage.py collectstatic --noinput --clear && \
gunicorn aprendecomigo.asgi:application ...
```

## Implementation Details

### Health Check Logic Flow

1. **Environment Detection**: Determine if running in Railway vs local
2. **Database Check**: Always required - fail fast if DB unavailable
3. **Redis Default Cache**: Test with retry logic
   - Railway: Required - fail if unavailable after retries  
   - Local: Optional - log warnings only
4. **Redis Sessions Cache**: Test with retry logic
   - Always critical since sessions are required for auth
5. **Configuration Validation**: Railway-specific Redis URL validation
6. **Response Generation**: Appropriate HTTP status based on overall health

### Error Handling Strategy

#### Connection Errors
```python
# Handles: ConnectionError, TimeoutError, socket errors
try:
    cache.set(test_key, test_value, timeout=30)
    result = cache.get(test_key)
except Exception as e:
    if is_railway:
        overall_healthy = False  # Fail in production
    else:
        logger.warning(f"Redis failed in dev: {e}")  # Continue locally
```

#### Retry Logic
```python
# 3 attempts with exponential backoff for Railway
max_retries = 3 if is_railway else 1
retry_delay = 1  # seconds, increases each attempt
```

### Monitoring and Observability

#### Logging Strategy
- `INFO`: Normal health check operations and successes
- `WARNING`: Redis issues in local development, degraded services
- `ERROR`: Critical failures that affect health check status

#### Metrics Available
- Attempt count for Redis connections
- Response times for each check
- Environment detection
- Configuration validation results

## Operational Guidelines

### Deployment Best Practices

1. **Use Simple Health Check for Railway**: Ensures faster startup and routing
2. **Monitor Detailed Health Check**: Use for operational monitoring
3. **Redis Service Dependencies**: Ensure Redis service is linked to Railway project
4. **Environment Variables**: Verify `REDIS_URL` is properly set

### Troubleshooting

#### Redis Connection Refused (Error 111)
1. Check if Redis service is running in Railway project
2. Verify `REDIS_URL` environment variable points to `redis.railway.internal`
3. Check Railway service linking between web app and Redis
4. Review Railway logs for Redis service startup

#### Health Check Always Returns 200
- **Before Fix**: Redis failures were marked as "degraded" but returned 200
- **After Fix**: Redis failures in Railway environment return 503

#### Monitoring Health Status
```bash
# Simple health check (Railway uses this)
curl https://your-app.railway.app/health/

# Detailed health check (for monitoring)
curl https://your-app.railway.app/health/detailed/
```

## Testing

### Local Testing
```bash
# Test with Redis available
python manage.py runserver
curl http://localhost:8000/health/
curl http://localhost:8000/health/detailed/

# Test with Redis unavailable (stop Redis locally)
# Simple health check should still pass
# Detailed health check should show Redis issues but not fail (local env)
```

### Railway Testing
```bash
# Check simple health endpoint
curl https://your-app.railway.app/health/

# Check detailed health with Redis status
curl https://your-app.railway.app/health/detailed/ | jq .

# Monitor logs for health check behavior
railway logs
```

## Migration Notes

### Changes Made
1. **Added retry logic** for Redis connections with exponential backoff
2. **Environment-specific behavior** (Railway vs local)
3. **Proper error handling** that fails fast for critical dependencies
4. **Configuration validation** for Railway Redis setup
5. **Two-tier health check system** for startup vs monitoring

### Backwards Compatibility
- Simple health check endpoint remains at `/health/` for Railway
- Detailed health check moved to `/health/detailed/` for monitoring
- All existing health check consumers continue to work

### Rollback Strategy
If issues occur, the health check can be reverted by restoring the previous `healthcheck.py` file, but this will reintroduce the Redis timing issues. Instead, consider:

1. Adjusting retry counts or timeout values
2. Temporarily using only simple health checks
3. Reviewing Redis service configuration in Railway

This implementation provides robust health checking while handling Railway's Redis timing issues effectively.