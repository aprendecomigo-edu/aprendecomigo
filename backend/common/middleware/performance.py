"""
Performance monitoring middleware for tracking response times and database queries.
"""

import time
import logging
from django.db import connection
from django.core.cache import cache
from django.conf import settings

# Set up performance logger
performance_logger = logging.getLogger('performance')


class PerformanceMonitoringMiddleware:
    """
    Middleware to track request performance metrics.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Start timing
        start_time = time.time()
        start_queries = len(connection.queries)
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        end_queries = len(connection.queries)
        query_count = end_queries - start_queries
        
        # Add response headers for debugging
        if settings.DEBUG:
            response['X-Response-Time'] = f"{response_time:.2f}ms"
            response['X-Query-Count'] = str(query_count)
        
        # Log slow requests
        if response_time > 1000:  # Log requests taking more than 1 second
            performance_logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {response_time:.2f}ms with {query_count} queries"
            )
        
        # Track API endpoint performance
        if request.path.startswith('/api/') or request.path.startswith('/education/'):
            self._track_endpoint_performance(request, response_time, query_count)
        
        return response
    
    def _track_endpoint_performance(self, request, response_time, query_count):
        """Track performance metrics for specific endpoints."""
        endpoint = f"{request.method}:{request.path}"
        
        # Store in cache for monitoring dashboard
        cache_key = f"perf_stats_{endpoint.replace('/', '_').replace(':', '_')}"
        
        # Get existing stats
        stats = cache.get(cache_key, {
            'total_requests': 0,
            'total_time': 0,
            'total_queries': 0,
            'max_time': 0,
            'min_time': float('inf')
        })
        
        # Update stats
        stats['total_requests'] += 1
        stats['total_time'] += response_time
        stats['total_queries'] += query_count
        stats['max_time'] = max(stats['max_time'], response_time)
        stats['min_time'] = min(stats['min_time'], response_time)
        stats['avg_time'] = stats['total_time'] / stats['total_requests']
        stats['avg_queries'] = stats['total_queries'] / stats['total_requests']
        
        # Cache for 1 hour
        cache.set(cache_key, stats, 60 * 60)
        
        # Log detailed performance data
        performance_logger.info(
            f"Endpoint performance: {endpoint} "
            f"- Time: {response_time:.2f}ms "
            f"- Queries: {query_count} "
            f"- Avg: {stats['avg_time']:.2f}ms"
        )


class DatabaseQueryLoggingMiddleware:
    """
    Middleware to log slow database queries for optimization.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Reset queries for this request
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Log slow queries
        for query in connection.queries[initial_queries:]:
            query_time = float(query['time'])
            if query_time > 0.05:  # Log queries taking more than 50ms
                performance_logger.warning(
                    f"Slow query ({query_time:.3f}s): {query['sql'][:200]}..."
                )
        
        return response


def get_performance_stats():
    """
    Get performance statistics for monitoring dashboard.
    """
    # This would typically be called from a monitoring view
    stats = {}
    
    # Get cache keys that match our performance pattern
    # Note: This is a simplified implementation
    # In production, consider using Redis SCAN or similar
    
    return stats