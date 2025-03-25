# Aprende Comigo

A School Management Platform for specialized training and tutoring centers.

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