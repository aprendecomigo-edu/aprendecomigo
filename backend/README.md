# Aprende Comigo Backend

Django REST Framework backend for the Aprende Comigo educational platform.

## Environment Configuration

The backend uses environment-specific settings to handle different deployment environments:

- **Development**: Local development environment (default)
- **Staging**: Pre-production testing environment
- **Production**: Live production environment
- **Testing**: Environment for running automated tests

### Setting the Environment

Set the `DJANGO_ENV` environment variable to specify which environment to use:

```bash
# Development (default if not set)
export DJANGO_ENV=development

# Staging
export DJANGO_ENV=staging

# Production
export DJANGO_ENV=production

# Testing
export DJANGO_ENV=testing
```

For persistent settings, add this to your `.env` file in the project root.

### Environment Variables

Copy `env.example` to `.env` in the project root and customize the values:

```bash
cp env.example .env
```

Key environment variables:

- `DJANGO_ENV`: Environment mode (development, staging, production, testing)
- `SECRET_KEY`: Django secret key (required for staging/production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (required for staging/production)
- `DATABASE_URL`: Database connection URL (required for production)
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of origins allowed to make cross-origin requests

See `env.example` for a full list of configurable variables.

## Getting Started

1. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest path/to/test.py

# Run with reused database (faster)
pytest --reuse-db
```
