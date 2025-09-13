#!/bin/bash

# Development Environment Setup Script
# Run this to set up a fresh development environment

set -e  # Exit on error

echo "🚀 Setting up Aprende Comigo development environment..."

# Check Python version
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 is required but not found"
    echo "Please install Python 3.13 first"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.13 -m venv .venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing development dependencies..."
pip install -r requirements/dev.txt

# Set up environment variables if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# Django Settings
DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database (optional for local development)
DATABASE_URL=postgresql://user:password@localhost:5432/aprendecomigo

# Stripe (optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis (for Channels)
REDIS_URL=redis://localhost:6379

# Email (uses console backend in development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOF
    echo "Please update .env with your actual values"
else
    echo ".env file already exists"
fi

# Set Django environment for commands
export DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development
export SECRET_KEY=${SECRET_KEY:-"dev-secret-key-for-local-development"}

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser prompt
echo ""
read -p "Would you like to create a superuser? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Run checks
echo "🔍 Running Django checks..."
python manage.py check

echo ""
echo "Development environment setup complete!"
echo ""
echo "To start developing:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Start the development server: ch django run"
echo "  3. In another terminal, start Redis: redis-server"
echo ""
echo "Useful commands:"
echo "  - Run tests: ch django test"
echo "  - Run linting: ch django lint"
echo "  - Run type checking: ch django typecheck"
echo "  - Check coverage: ch django cov"
