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

See `env.example` for a full list of configurable variables.

---

# Aprende Comigo

A School Management Platform for specialized training and tutoring centers.

## App Architecture

The application is built with a modular structure using multiple Django apps that work together to provide the full functionality.

## API Documentation

The application uses Django REST Framework (DRF) to provide a full-featured API. The API supports authentication, serialization, and provides comprehensive documentation.

### API Endpoints

The API root is accessible at `/api/`, which provides links to all available resources.

### Interactive Documentation

Two different documentation interfaces are available:

1. **Swagger UI** - Available at `/api/swagger/`
   - Interactive documentation with request/response examples
   - Allows testing API endpoints directly in the browser
   - Shows all parameters, request bodies, and response formats
   - Ideal for developers and testing

2. **ReDoc** - Available at `/api/redoc/`
   - Clean, three-panel documentation layout
   - User-friendly navigation and design
   - Excellent readability for complex APIs
   - Better for non-technical users and general reference

### Authentication

The API uses JWT (JSON Web Token) for authentication. To authenticate:

1. Request an email verification code at `/api/auth/request-code/`
2. Verify the code at `/api/auth/verify-code/`
3. Use the returned token in the Authorization header for subsequent requests

Example:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Available Resources

- Users: `/api/users/`
- Teachers: `/api/teachers/`
- Students: `/api/students/`
- Scheduling (Classes): `/api/scheduling/`
- Financial: `/api/financials/`

### Google Calendar Data Format

- Calendars are created and managed in the admin's Google account (not through our application)
- Two calendars (online/in-person) are used for billing purposes
- Calendar event structure:
  - **Event title**: Student name (with "FALTOU" if absent)
  - **Start/end times**: Used for duration calculation
  - **Location**: Contains the teacher's name
  - **Description**: Contains a price code (hourly rate)

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
# On Unix or MacOS
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure PostgreSQL database:
- Create a database named `aprendecomigo`
- Update credentials in `.env` file if needed

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```
test@aprendecomigo.pt
Pass12345!

## Development Commands

- **Run the server**: `python manage.py runserver`
- **Apply migrations**: `python manage.py migrate`
- **Run all tests**: `python manage.py test`
- **Test a specific app**: `python manage.py test <app>`
- **Lint code**: `ruff check .`
- **Type check**: `mypy .`

## Google Calendar Integration (FUTURE)

### Development Environment Setup

To enable Google Calendar integration in your development environment, follow these steps:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials
   - Set Authorized JavaScript origins to: `http://localhost:8000`
   - Set Authorized redirect URIs to: `http://localhost:8000/accounts/google/login/callback/`
5. Download the client ID and client secret
6. In the Django admin panel:
   - Go to Sites and update the example.com domain to `localhost:8000`
   - Go to Social applications and add a new one:
     - Provider: Google
     - Name: Google
     - Client id: (from your Google console)
     - Secret key: (from your Google console)
     - Sites: Add `localhost:8000`

### Production Environment Setup

For production deployment, you'll need to follow these additional steps:

1. In the Google Cloud Console:
   - Go to your project's OAuth consent screen
   - Set the User Type to "External" (or "Internal" if this is for organization use only)
   - Complete all required fields (app name, user support email, developer contact)
   - Add the scopes: `openid`, `profile`, `email`, `https://www.googleapis.com/auth/calendar`, and `https://www.googleapis.com/auth/calendar.events`
   - Add your production domain to the Authorized Domains list

2. For your OAuth credentials:
   - Add your production domain (e.g., `https://yourdomain.com`) to Authorized JavaScript Origins
   - Add your callback URL (e.g., `https://yourdomain.com/accounts/google/login/callback/`) to Authorized Redirect URIs
   - If you're using multiple environments (staging, testing, etc.), add entries for each

3. If you're moving from development to production:
   - You'll need to go through Google's OAuth verification process if your app is public
   - This may include adding a privacy policy URL, terms of service URL, and potentially submitting for review

4. In your production Django admin panel:
   - Log in to the Django admin panel on your production server
   - Go to Sites and add your production domain (e.g., `yourdomain.com`)
   - Go to Social Applications and add a new one with your production credentials
     - Provider: Google
     - Name: Google (or something more specific like "Google Calendar Production")
     - Client ID: Your production client ID
     - Secret key: Your production client secret
     - Sites: Select your production domain

5. Security considerations:
   - Store your production client secret securely (use environment variables)
   - Ensure your site uses HTTPS for all OAuth flows
   - Implement strict CSRF protections
   - Regularly rotate your OAuth credentials

Remember that Google OAuth requires a valid top-level domain for production use. IP addresses and localhost will only work for development.

Once configured, users will be able to login with their Google account and grant calendar access.

## Running with HTTPS (for Google OAuth)

When developing with Google OAuth, you need HTTPS even on your local development server. This project uses django-sslserver to enable HTTPS in development.

### Setup

1. Install requirements which include django-sslserver:
   ```
   pip install -r requirements.txt
   ```

2. Configure Google OAuth in Google Cloud Console:
   - Add `https://localhost:8000/accounts/google/login/callback/` as an authorized redirect URI
   - Add `https://localhost:8000` as an authorized JavaScript origin

3. Run the server with SSL:
   ```
   python manage.py runsslserver
   ```

4. Access your site at `https://localhost:8000`

Note: You'll need to accept the self-signed certificate in your browser on first access.

## Running the application

```bash
python manage.py runserver
```
test@aprendecomigo.pt
Pass12345!

The site will be available at http://127.0.0.1:8000/

## Running Tests

### Unit Tests

To run all unit tests:

```bash
python manage.py test accounts scheduling
```

Or with pytest:

```bash
pytest accounts scheduling
```

### Functional Tests

To run functional tests with Selenium:

```bash
python manage.py test functional_tests.py
```

Or with pytest:

```bash
pytest functional_tests.py
```

**Note:** Functional tests require a web driver installed. The tests are configured to use Chrome by default with a fallback to Firefox if Chrome is not available.

#### Installing WebDrivers:

- **Chrome:** Download ChromeDriver from https://chromedriver.chromium.org/downloads matching your Chrome version
- **Firefox:** Download GeckoDriver from https://github.com/mozilla/geckodriver/releases

Make sure the driver executable is in your system's PATH.

## Test Coverage

To generate a test coverage report:

1. Install coverage:
```bash
pip install coverage
```

2. Run tests with coverage:
```bash
coverage run --source='.' manage.py test accounts scheduling
```

3. Generate a report:
```bash
coverage report
```

4. Generate an HTML report (optional):
```bash
coverage html
```

The HTML report will be available in the `htmlcov` directory.
