"""
Custom Redis connection factory for Railway's IPv6 network.
Railway uses IPv6-only internal networking, requiring special handling.
"""
import socket
from django_redis.pool import ConnectionFactory


class RailwayIPv6ConnectionFactory(ConnectionFactory):
    """
    Custom connection factory for Railway's IPv6 network.
    
    Railway's internal network is IPv6-only, so we need to ensure
    that redis-py creates connections that can handle IPv6 addresses.
    """
    
    def make_connection_params(self, url):
        """Override to add IPv6 support to connection parameters."""
        params = super().make_connection_params(url)
        
        # Add IPv6-friendly connection parameters
        # These go directly to the connection, not in CONNECTION_POOL_KWARGS
        params.update({
            'socket_type': socket.AF_UNSPEC,  # Support both IPv4 and IPv6
            'socket_connect_timeout': 10,
            'socket_timeout': 10,
            'socket_keepalive': True,
        })
        
        # Remove CONNECTION_POOL_KWARGS from connection params
        # They should only be used for pool creation, not connection creation
        params.pop('CONNECTION_POOL_KWARGS', None)
        
        return params