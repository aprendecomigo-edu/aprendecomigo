.PHONY: dev dev-open backend frontend stop logs open health check-deps

backend:
	@echo "Starting Django backend server..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; exit 1; fi
	cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver

frontend:
	@echo "Starting Expo frontend server..."
	cd frontend-ui && EXPO_PUBLIC_ENV=development npx expo start --web

dev:
	@echo "Starting development servers..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"; exit 1; fi
	@mkdir -p logs
	@echo "Backend logs: logs/backend.log"
	@echo "Frontend logs: logs/frontend.log"
	@echo "Stopping any existing servers on ports 8000 and 8081..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:8081 | xargs kill -9 2>/dev/null || true
	@sleep 2
	@echo "Please wait while servers start up..."
	@echo "Starting backend server..."
	@(cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver > ../logs/backend.log 2>&1) & \
	echo $$! > logs/backend.pid
	@sleep 3
	@echo "Starting frontend server..."
	@(cd frontend-ui && EXPO_PUBLIC_ENV=development npx expo start --web > ../logs/frontend.log 2>&1) & \
	echo $$! > logs/frontend.pid
	@sleep 8 && echo "Servers should be ready!" && \
	echo "Frontend: http://localhost:8081" && \
	echo "Backend API: http://localhost:8000/api/" && \
	echo "View logs: make logs" && \
	echo "Stop servers: make stop" && \
	echo "Open browser: make open"
	@echo "Press Ctrl+C to stop servers"
	@trap 'make stop' INT; while true; do sleep 1; done

dev-open:
	@echo "Starting development servers with auto-browser opening..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"; exit 1; fi
	@mkdir -p logs
	@echo "Backend logs: logs/backend.log"
	@echo "Frontend logs: logs/frontend.log"
	@echo "Stopping any existing servers on ports 8000 and 8081..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:8081 | xargs kill -9 2>/dev/null || true
	@sleep 2
	@echo "Please wait while servers start up..."
	@echo "Starting backend server..."
	@(cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver > ../logs/backend.log 2>&1) & \
	echo $$! > logs/backend.pid
	@sleep 3
	@echo "Starting frontend server..."
	@(cd frontend-ui && EXPO_PUBLIC_ENV=development npx expo start --web > ../logs/frontend.log 2>&1) & \
	echo $$! > logs/frontend.pid
	@sleep 8 && echo "Servers should be ready!" && \
	echo "Frontend: http://localhost:8081" && \
	echo "Backend API: http://localhost:8000/api/" && \
	echo "View logs: make logs" && \
	echo "Stop servers: make stop" && \
	sleep 2 && make open
	@echo "Press Ctrl+C to stop servers"
	@trap 'make stop' INT; while true; do sleep 1; done

open:
	@echo "Opening frontend in browser..."
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8081; \
		echo "Browser opened (macOS)"; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8081; \
		echo "Browser opened (Linux)"; \
	elif command -v start >/dev/null 2>&1; then \
		start http://localhost:8081; \
		echo "Browser opened (Windows)"; \
	else \
		echo "Could not detect browser opener. Please manually visit: http://localhost:8081"; \
	fi

logs:
	@echo "Development Server Logs"
	@echo "=========================="
	@if [ ! -d "logs" ]; then echo "No logs directory found. Run 'make dev' first."; exit 1; fi
	@if [ ! -f "logs/backend.log" ] && [ ! -f "logs/frontend.log" ]; then echo "No log files found. Make sure servers are running."; exit 1; fi
	@echo "Backend Log (last 10 lines):"
	@echo "--------------------------------"
	@if [ -f "logs/backend.log" ]; then tail -10 logs/backend.log 2>/dev/null || echo "No backend log content"; else echo "Backend log not found"; fi
	@echo ""
	@echo "Frontend Log (last 10 lines):"
	@echo "---------------------------------"
	@if [ -f "logs/frontend.log" ]; then tail -10 logs/frontend.log 2>/dev/null || echo "No frontend log content"; else echo "Frontend log not found"; fi
	@echo ""
	@echo "For live logs: tail -f logs/backend.log logs/frontend.log"
	@echo "For full logs: cat logs/backend.log logs/frontend.log"

stop:
	@echo "Stopping development servers..."
	@if [ -f "logs/backend.pid" ]; then \
		kill -TERM $$(cat logs/backend.pid) 2>/dev/null || true; \
		rm -f logs/backend.pid; \
	fi
	@if [ -f "logs/frontend.pid" ]; then \
		kill -TERM $$(cat logs/frontend.pid) 2>/dev/null || true; \
		rm -f logs/frontend.pid; \
	fi
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:8081 | xargs kill -9 2>/dev/null || true
	@pkill -f "python3 manage.py runserver" || true
	@pkill -f "python manage.py runserver" || true
	@pkill -f "python.*manage.py" || true
	@pkill -f "expo start" || true
	@echo "Servers stopped"

health:
	@echo "Checking server health..."
	@echo "Backend status:"
	@curl -s http://localhost:8000/api/ > /dev/null && echo "✓ Backend (8000) - OK" || echo "✗ Backend (8000) - DOWN"
	@echo "Frontend status:"
	@curl -s http://localhost:8081 > /dev/null && echo "✓ Frontend (8081) - OK" || echo "✗ Frontend (8081) - DOWN"

check-deps:
	@echo "Checking dependencies..."
	@echo "Python virtual environment:"
	@if [ -d ".venv" ]; then echo "✓ Virtual environment exists"; else echo "✗ Virtual environment missing"; fi
	@if [ -d ".venv" ]; then source .venv/bin/activate && python3 --version; fi
	@echo "Frontend dependencies:"
	@cd frontend-ui && npm list --depth=0 expo || echo "✗ Expo not installed properly"
	@echo "Environment variables:"
	@echo "DJANGO_ENV: $${DJANGO_ENV:-not set}"
	@echo "EXPO_PUBLIC_ENV: $${EXPO_PUBLIC_ENV:-not set}"
