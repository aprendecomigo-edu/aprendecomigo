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
import shlex
import subprocess  # nosec B404 - Subprocess usage is secure with input validation
from urllib.parse import urlparse


def run_railway_command(cmd):
    """
    Run a Railway CLI command with security validation.

    Args:
        cmd: Railway CLI command string (must start with 'railway')

    Returns:
        str: Command output or None if command failed/invalid

    Security:
        - Only allows 'railway' commands
        - Uses shlex.split() for proper argument parsing
        - Validates command structure before execution
    """
    if not isinstance(cmd, str):
        print("❌ Security Error: Command must be a string")
        return None

    # Security check: only allow Railway CLI commands
    cmd = cmd.strip()
    if not cmd.startswith("railway "):
        print("❌ Security Error: Only 'railway' commands are allowed")
        return None

    # Additional security: validate command structure
    allowed_subcommands = {"variables", "up", "status", "logs", "help"}
    try:
        # Use shlex.split for proper shell argument parsing
        args = shlex.split(cmd)
        if len(args) < 2 or args[1] not in allowed_subcommands:
            print(f"❌ Security Error: Subcommand '{args[1] if len(args) > 1 else 'none'}' not allowed")
            return None
    except ValueError as e:
        print(f"❌ Security Error: Invalid command syntax: {e}")
        return None

    try:
        # Use shlex.split() instead of cmd.split() for better security
        result = subprocess.run(  # nosec B603 - Input is validated and whitelisted
            args,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,  # Add timeout to prevent hanging
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("❌ Railway CLI error: Command timed out after 30 seconds")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Railway CLI error: {e}")
        return None
    except FileNotFoundError:
        print("❌ Railway CLI error: Railway CLI not found. Please install it first.")
        return None


def check_database_variables():
    """Check database environment variables for optimization opportunities."""
    print("\n🗄️  DATABASE CONFIGURATION ANALYSIS")
    print("-" * 50)

    # Check if we have problematic public URLs
    issues = []
    recommendations = []

    database_url = os.environ.get("DATABASE_URL")
    database_public_url = os.environ.get("DATABASE_PUBLIC_URL")

    if database_url:
        parsed = urlparse(database_url)
        print(f"📍 DATABASE_URL host: {parsed.hostname}")

        if ".railway.internal" in parsed.hostname:
            print("   ✅ Using private networking (good!)")
        elif ".proxy.rlwy.net" in parsed.hostname:
            print("   🚨 Using public proxy (costs money!)")
            issues.append("DATABASE_URL uses public proxy endpoint")
            recommendations.append("Update DATABASE_URL to use .railway.internal domain")

    if database_public_url:
        print("⚠️  DATABASE_PUBLIC_URL detected - avoid using this variable")
        issues.append("DATABASE_PUBLIC_URL should not be used in application code")
        recommendations.append("Use DATABASE_URL with private domain instead")

    # Check individual PG variables
    pg_vars = ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGPORT"]
    pg_config_complete = all(os.environ.get(var) for var in pg_vars)

    if pg_config_complete:
        pghost = os.environ.get("PGHOST")
        print(f"📍 PGHOST: {pghost}")

        if ".railway.internal" in pghost:
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

    redis_url = os.environ.get("REDIS_URL")

    if redis_url:
        parsed = urlparse(redis_url)
        print(f"📍 REDIS_URL host: {parsed.hostname}")

        if ".railway.internal" in parsed.hostname:
            print("   ✅ Using private networking")
        elif ".proxy.rlwy.net" in parsed.hostname:
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
