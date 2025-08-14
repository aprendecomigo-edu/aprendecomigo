.PHONY: dev dev-prod stop logs health lint test test-fast test-parallel test-coverage create-test-data verify-test-data create-admin-calendar migrate shell

# Development server commands
dev:
	@echo "Starting Django development server..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; exit 1; fi
	@mkdir -p logs
	@TIMESTAMP=$$(date +"%Y%m%d-%H%M%S"); \
	echo "Stopping any existing servers on port 8000..."; \
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true; \
	sleep 1; \
	echo "Starting server..."; \
	(source .venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver > logs/server-$$TIMESTAMP.log 2>&1) & \
	echo $$! > logs/server.pid; \
	sleep 3; \
	echo "Django server ready at http://localhost:8000/api/"; \
	echo "Admin panel: http://localhost:8000/admin/"; \
	echo "View logs: make logs"; \
	echo "Stop server: make stop"
	@trap 'make stop' INT; while true; do sleep 1; done

dev-prod:
	@echo "Starting Django with Daphne (production-like)..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; exit 1; fi
	source .venv/bin/activate && DJANGO_ENV=development DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development daphne -b 0.0.0.0 -p 8000 aprendecomigo.asgi:application

stop:
	@echo "Stopping Django server..."
	@if [ -f "logs/server.pid" ]; then \
		kill -TERM $$(cat logs/server.pid) 2>/dev/null || true; \
		rm -f logs/server.pid; \
	fi
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@pkill -f "python manage.py runserver" || true
	@pkill -f "python.*manage.py" || true
	@pkill -f "daphne.*aprendecomigo" || true
	@echo "Server stopped"

logs:
	@echo "Django Server Logs"
	@echo "=================="
	@if [ ! -d "logs" ]; then echo "No logs directory found. Run 'make dev' first."; exit 1; fi
	@LATEST_LOG=$$(ls -t logs/server-*.log 2>/dev/null | head -1); \
	if [ -z "$$LATEST_LOG" ]; then \
		echo "No log files found. Make sure server is running."; exit 1; \
	fi; \
	echo "Latest log: $$LATEST_LOG"; \
	echo "--------------------------------"; \
	tail -20 "$$LATEST_LOG"; \
	echo ""; \
	echo "For live logs: tail -f $$LATEST_LOG"

health:
	@echo "Checking Django server health..."
	@curl -s http://localhost:8000/api/ > /dev/null && echo "✓ API (8000) - OK" || echo "✗ API (8000) - DOWN"
	@curl -s http://localhost:8000/admin/ > /dev/null && echo "✓ Admin panel - OK" || echo "✗ Admin panel - DOWN"

# Testing commands
test:
	@echo "Running Django tests..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.testing python3 manage.py test --noinput

test-fast:
	@echo "Running Django tests (optimized for development)..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.testing python3 manage.py test --noinput

test-parallel:
	@echo "Running Django tests in parallel..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.testing python3 manage.py test --noinput --parallel

test-coverage:
	@echo "Running Django tests with coverage..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.testing coverage run --source='.' manage.py test --noinput && coverage report

# Code quality
lint:
	@echo "Running Python linting..."
	@source .venv/bin/activate && \
		pip install flake8 > /dev/null 2>&1 && \
		echo "Checking for syntax errors and undefined names..." && \
		flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics \
			--exclude=.venv,venv,migrations,__pycache__,.git,build,dist && \
		echo "✓ Critical linting checks passed!" && \
		echo "Running additional style checks..." && \
		flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics \
			--exclude=.venv,venv,migrations,__pycache__,.git,build,dist

# Database and data management
migrate:
	@echo "Running Django migrations..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development python3 manage.py migrate

shell:
	@echo "Opening Django shell..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development python3 manage.py shell

create-test-data:
	@echo "Creating school admin test data..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development python3 manage.py create_school_admin_test_data --clear-existing
	@echo "Test data created successfully!"
	@echo "Admin email: ana.silva@example.com"
	@echo "Verify data with: make verify-test-data"

verify-test-data:
	@echo "Verifying school admin test data..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development python3 manage.py verify_test_data

create-admin-calendar:
	@echo "Creating admin calendar events..."
	@source .venv/bin/activate && DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development python3 manage.py create_admin_calendar_events --school-admin-email ana.silva@example.com
	@echo "Admin calendar events created successfully!"

# Installation and setup
install:
	@echo "Installing Python dependencies..."
	@if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
	@source .venv/bin/activate && pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

setup: install migrate
	@echo "Backend setup complete!"
	@echo "Run 'make dev' to start the development server"

# Help
help:
	@echo "Available commands:"
	@echo "  make dev           - Start development server"
	@echo "  make dev-prod      - Start with Daphne (production-like)"
	@echo "  make stop          - Stop the server"
	@echo "  make logs          - View server logs"
	@echo "  make health        - Check server health"
	@echo "  make test          - Run all tests"
	@echo "  make test-fast     - Run tests (optimized)"
	@echo "  make test-parallel - Run tests in parallel"
	@echo "  make test-coverage - Run tests with coverage"
	@echo "  make lint          - Run code linting"
	@echo "  make migrate       - Run database migrations"
	@echo "  make shell         - Open Django shell"
	@echo "  make install       - Install dependencies"
	@echo "  make setup         - Complete setup (install + migrate)"