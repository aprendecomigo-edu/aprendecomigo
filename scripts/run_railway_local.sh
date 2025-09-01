#!/bin/bash
# Simulate Railway environment locally for testing

echo "🚂 Starting Railway-like local environment..."

# Set Railway-like environment variables
export DJANGO_ENV=staging
export DEBUG=True
export SECRET_KEY=django-insecure-local-railway-test-key-12345
export ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Use local PostgreSQL (install with: brew install postgresql)
export DATABASE_URL=postgresql://localhost/aprendecomigo_staging

# Run with uvicorn like Railway does
echo "📦 Running uvicorn (same as Railway)..."
uvicorn aprendecomigo.asgi:application --host 127.0.0.1 --port 8000 --reload

echo "🌍 Visit: http://localhost:8000"
echo "📊 Health check: http://localhost:8000/health/"