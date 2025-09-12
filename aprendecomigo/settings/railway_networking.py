"""
Railway Private Networking Optimization
Implements best practices for internal service communication to avoid egress fees.
"""

import os
import socket
from urllib.parse import urlparse


def get_optimized_database_config():
    """
    Get optimized database configuration using Railway's private networking.
    
    Priority:
    1. Use individual PG* variables for explicit private networking
    2. Fall back to DATABASE_URL (should be private)
    3. Never use DATABASE_PUBLIC_URL (incurs egress fees)
    """
    
    # Method 1: Explicit private networking using individual variables (RECOMMENDED)
    if all(os.environ.get(var) for var in ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']):
        print("🔒 Using explicit private networking configuration")
        
        db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['PGDATABASE'],
            'USER': os.environ['PGUSER'],
            'PASSWORD': os.environ['PGPASSWORD'],
            'HOST': os.environ['PGHOST'],  # Should be *.railway.internal
            'PORT': os.environ.get('PGPORT', '5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
                # PostgreSQL specific options (not MAX_CONNS which is invalid)
                'options': '-c default_transaction_isolation=read-committed',
                'application_name': 'aprendecomigo_staging',
            }
        }
        
        # Verify we're using private domain
        host = db_config['HOST']
        if '.railway.internal' in host:
            print(f"✅ Using private domain: {host}")
        elif '.proxy.rlwy.net' in host:
            print(f"⚠️  WARNING: Using public proxy domain: {host} - This will incur egress fees!")
        else:
            print(f"❓ Unknown domain pattern: {host}")
        
        return db_config
    
    # Method 2: DATABASE_URL fallback (should be private)
    elif os.environ.get('DATABASE_URL'):
        import dj_database_url
        
        database_url = os.environ['DATABASE_URL']
        parsed = urlparse(database_url)
        
        print(f"🔄 Using DATABASE_URL with host: {parsed.hostname}")
        
        # Verify it's private networking
        if '.railway.internal' in parsed.hostname:
            print("✅ DATABASE_URL uses private networking")
        elif '.proxy.rlwy.net' in parsed.hostname:
            print("🚨 ERROR: DATABASE_URL uses public proxy - This will incur egress fees!")
            print("💡 Consider using individual PG* variables instead")
        
        return dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    
    else:
        raise ValueError("No database configuration found. Set PGHOST, PGDATABASE, PGUSER, PGPASSWORD or DATABASE_URL")


def get_optimized_redis_config():
    """
    Get optimized Redis configuration for Railway private networking.
    We already have good IPv6 support in redis_ipv6.py
    """
    redis_url = os.environ.get('REDIS_URL', '')
    
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is not set")
    
    parsed = urlparse(redis_url)
    
    print(f"🔄 Redis configuration: {parsed.hostname}")
    
    # Verify private networking
    if '.railway.internal' in parsed.hostname:
        print("✅ Redis uses private networking")
    elif '.proxy.rlwy.net' in parsed.hostname:
        print("⚠️  WARNING: Redis uses public proxy - consider switching to private domain")
    
    return redis_url


def verify_ipv6_support():
    """
    Verify IPv6 support since Railway's private network is IPv6-only.
    """
    try:
        # Test IPv6 socket creation
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.close()
        print("✅ IPv6 support available")
        return True
    except Exception as e:
        print(f"⚠️  IPv6 support issue: {e}")
        return False


def print_networking_summary():
    """
    Print a summary of networking configuration for debugging.
    """
    print("\n" + "="*60)
    print("🌐 RAILWAY NETWORKING CONFIGURATION SUMMARY")
    print("="*60)
    
    # Database
    pghost = os.environ.get('PGHOST', 'Not set')
    database_url = os.environ.get('DATABASE_URL', 'Not set')
    
    print(f"🗄️  PGHOST: {pghost}")
    if '.railway.internal' in pghost:
        print("   ✅ Private networking")
    elif '.proxy.rlwy.net' in pghost:
        print("   🚨 Public proxy (egress fees)")
    
    # Redis
    redis_url = os.environ.get('REDIS_URL', 'Not set')
    if redis_url != 'Not set':
        parsed = urlparse(redis_url)
        print(f"📦 Redis host: {parsed.hostname}")
        if '.railway.internal' in parsed.hostname:
            print("   ✅ Private networking")
    
    # IPv6
    ipv6_ok = verify_ipv6_support()
    print(f"🌐 IPv6 support: {'✅ Available' if ipv6_ok else '❌ Issues detected'}")
    
    print("="*60 + "\n")