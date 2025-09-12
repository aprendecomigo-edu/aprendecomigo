#!/usr/bin/env python3
"""
Railway Private Networking Optimization Script

This script helps optimize Railway environment variables for:
1. Cost efficiency (avoid egress fees)
2. Performance (use private networking)
3. Security (internal communication only)

Usage:
python scripts/optimize_railway_networking.py
"""

import os
import subprocess
import json
from urllib.parse import urlparse


def run_railway_command(cmd):
    """Run a Railway CLI command and return the output."""
    try:
        result = subprocess.run(
            cmd.split(), 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Railway CLI error: {e}")
        return None


def check_database_variables():
    """Check database environment variables for optimization opportunities."""
    print("\n🗄️  DATABASE CONFIGURATION ANALYSIS")
    print("-" * 50)
    
    # Check if we have problematic public URLs
    issues = []
    recommendations = []
    
    database_url = os.environ.get('DATABASE_URL')
    database_public_url = os.environ.get('DATABASE_PUBLIC_URL')
    
    if database_url:
        parsed = urlparse(database_url)
        print(f"📍 DATABASE_URL host: {parsed.hostname}")
        
        if '.railway.internal' in parsed.hostname:
            print("   ✅ Using private networking (good!)")
        elif '.proxy.rlwy.net' in parsed.hostname:
            print("   🚨 Using public proxy (costs money!)")
            issues.append("DATABASE_URL uses public proxy endpoint")
            recommendations.append("Update DATABASE_URL to use .railway.internal domain")
    
    if database_public_url:
        print(f"⚠️  DATABASE_PUBLIC_URL detected - avoid using this variable")
        issues.append("DATABASE_PUBLIC_URL should not be used in application code")
        recommendations.append("Use DATABASE_URL with private domain instead")
    
    # Check individual PG variables
    pg_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD', 'PGPORT']
    pg_config_complete = all(os.environ.get(var) for var in pg_vars)
    
    if pg_config_complete:
        pghost = os.environ.get('PGHOST')
        print(f"📍 PGHOST: {pghost}")
        
        if '.railway.internal' in pghost:
            print("   ✅ Individual PG variables use private networking")
        else:
            issues.append("PGHOST doesn't use .railway.internal domain")
    
    return issues, recommendations


def check_redis_variables():
    """Check Redis configuration."""
    print("\n📦 REDIS CONFIGURATION ANALYSIS")
    print("-" * 50)
    
    issues = []
    recommendations = []
    
    redis_url = os.environ.get('REDIS_URL')
    
    if redis_url:
        parsed = urlparse(redis_url)
        print(f"📍 REDIS_URL host: {parsed.hostname}")
        
        if '.railway.internal' in parsed.hostname:
            print("   ✅ Using private networking")
        elif '.proxy.rlwy.net' in parsed.hostname:
            print("   ⚠️  Using public proxy (potential egress fees)")
            issues.append("REDIS_URL uses public proxy endpoint")
            recommendations.append("Update REDIS_URL to use .railway.internal domain")
    else:
        issues.append("REDIS_URL not found")
    
    return issues, recommendations


def suggest_optimizations():
    """Provide optimization suggestions based on Railway best practices."""
    print("\n💡 OPTIMIZATION SUGGESTIONS")
    print("-" * 50)
    
    suggestions = [
        "Use reference variables: DATABASE_URL=${{postgres.RAILWAY_PRIVATE_DOMAIN}}:${{postgres.PGPORT}}/railway",
        "Ensure all service-to-service communication uses .railway.internal domains",
        "Bind services to IPv6 (::) for dual-stack support",
        "Set explicit PORT variables for services that need them",
        "Use http:// (not https://) for internal service communication",
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")


def generate_railway_commands():
    """Generate Railway CLI commands for optimization."""
    print("\n🚀 RAILWAY CLI OPTIMIZATION COMMANDS")
    print("-" * 50)
    
    commands = [
        "# Check current service variables:",
        "railway variables",
        "",
        "# If you need to set explicit PostgreSQL port:",
        "railway variables --service postgres-service-name set PORT=5432",
        "",
        "# Verify private domain usage:",
        "railway variables | grep RAILWAY_PRIVATE_DOMAIN",
        "",
        "# Deploy with optimized configuration:",
        "railway up",
    ]
    
    for cmd in commands:
        print(cmd)


def main():
    print("🚄 Railway Private Networking Optimization")
    print("=" * 60)
    
    # Check current configuration
    db_issues, db_recommendations = check_database_variables()
    redis_issues, redis_recommendations = check_redis_variables()
    
    # Summary
    print("\n📋 OPTIMIZATION SUMMARY")
    print("-" * 50)
    
    all_issues = db_issues + redis_issues
    all_recommendations = db_recommendations + redis_recommendations
    
    if all_issues:
        print("🚨 Issues found:")
        for issue in all_issues:
            print(f"   • {issue}")
        
        print("\n💡 Recommendations:")
        for rec in all_recommendations:
            print(f"   • {rec}")
    else:
        print("✅ Configuration looks good!")
    
    suggest_optimizations()
    generate_railway_commands()
    
    print("\n🔗 Additional Resources:")
    print("• Railway Private Networking: https://docs.railway.com/guides/private-networking")
    print("• IPv6 Support: https://docs.railway.com/guides/ipv6")


if __name__ == "__main__":
    main()