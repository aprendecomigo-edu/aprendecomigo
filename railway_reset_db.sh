#!/bin/bash
# Railway Database Reset Script
# This script will be run on Railway to reset the PostgreSQL database

echo "🚄 Starting Railway database reset..."
echo "Using optimized private networking configuration"

# Run the reset command with --force flag (no prompts on Railway)
python manage.py reset_db --force

echo "✅ Database reset completed!"

# Show the networking configuration
echo ""
echo "🌐 Railway networking configuration:"
python manage.py check_db