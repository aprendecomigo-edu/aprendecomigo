# Requirements Management Guide

## 📁 Structure

```
requirements/
├── base.txt     # Core dependencies needed everywhere
├── dev.txt      # Development & testing tools (includes base.txt)
├── prod.txt     # Production optimizations (includes base.txt)
└── README.md    # This file
```

## 🚀 Quick Start

### For Development (Most Common)
```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements/dev.txt
```

### For Production
```bash
# Install production dependencies only
pip install -r requirements/prod.txt
```

### For Testing/CI
```bash
# Use dev.txt for CI/CD as well - includes all testing tools
pip install -r requirements/dev.txt
```

## 📦 What's in Each File?

### `base.txt` - Core Dependencies
- Django & Django REST Framework
- Database drivers (PostgreSQL)
- Channels & WebSocket support (Uvicorn)
- Authentication (Knox, JWT)
- Payment processing (Stripe)
- Essential utilities

**When to use**: Never directly - always through dev.txt, prod.txt, or test.txt

### `dev.txt` - Development Environment
Includes everything from base.txt PLUS:
- **Type checking**: mypy, django-stubs
- **Linting**: ruff
- **Testing**: coverage
- **Security**: pip-audit
- **Development utilities**: rich, pygments

**When to use**: Local development on your machine

### `prod.txt` - Production Environment
Includes everything from base.txt PLUS:
- Production-optimized database drivers
- Monitoring tools (optional)
- Performance optimizations

**When to use**: Deployment to servers (Heroku, AWS, etc.)


## 🛠️ Common Commands

### Update a specific environment
```bash
# After adding a package to base.txt
pip install -r requirements/dev.txt  # Reinstalls everything

# Freeze current environment (be careful!)
pip freeze > requirements/current.txt
```

### Add a new package
```bash
# 1. Install it
pip install package-name

# 2. Add to appropriate file:
# - If needed everywhere → base.txt
# - If only for development → dev.txt
# - If only for production → prod.txt

# 3. Pin the version
echo "package-name==1.2.3" >> requirements/base.txt
```

### Check for security issues
```bash
pip-audit
```

### Check for outdated packages
```bash
pip list --outdated
```

## 🔄 Migration from Single requirements.txt

If you're migrating from a single requirements.txt:

```bash
# Backup current environment
pip freeze > requirements.backup.txt

# Clean install with new structure
pip install -r requirements/dev.txt

# Verify everything works
python manage.py check
python manage.py test
```

## ⚠️ Important Notes

1. **Always use virtual environments** to avoid conflicts
2. **Pin versions** (use ==) for reproducible builds
3. **Regularly update** dependencies for security patches
4. **Test after updates** - especially major version changes

## 🤔 Decision Tree: Which File to Use?

```
Are you...
├── Writing code locally? → requirements/dev.txt
├── Running tests in CI/CD? → requirements/dev.txt
├── Deploying to production? → requirements/prod.txt
└── Just need core functionality? → requirements/base.txt (via one of the above)
```

## 📝 Environment Variables

Different environments may need different settings:

```bash
# Development
export DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development

# Production
export DJANGO_SETTINGS_MODULE=aprendecomigo.settings.production

# Testing
export DJANGO_SETTINGS_MODULE=aprendecomigo.settings.testing
```