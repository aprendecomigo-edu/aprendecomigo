.PHONY: dev dev-open backend frontend stop logs open

backend:
	@echo "Starting Django backend server..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; exit 1; fi
	cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver

frontend:
	@echo "Starting Expo frontend server..."
	cd frontend-ui && EXPO_PUBLIC_ENV=development npm run web:dev

dev:
	@echo "Starting development servers..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"; exit 1; fi
	@mkdir -p logs
	@echo "Backend logs: logs/backend.log"
	@echo "Frontend logs: logs/frontend.log"
	@echo "Please wait while servers start up..."
	(cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver > ../logs/backend.log 2>&1) & \
	(cd frontend-ui && EXPO_PUBLIC_ENV=development npx expo start --web > ../logs/frontend.log 2>&1) & \
	sleep 8 && echo "Servers should be ready!" && \
	echo "Frontend: http://localhost:8081" && \
	echo "Backend API: http://localhost:8000/api/" && \
	echo "View logs: make logs" && \
	echo "Stop servers: make stop" && \
	echo "Open browser: make open" && \
	wait

dev-open:
	@echo "Starting development servers with auto-browser opening..."
	@if [ ! -d ".venv" ]; then echo "Virtual environment not found at .venv"; echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"; exit 1; fi
	@mkdir -p logs
	@echo "Backend logs: logs/backend.log"
	@echo "Frontend logs: logs/frontend.log"
	@echo "Please wait while servers start up..."
	(cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver > ../logs/backend.log 2>&1) & \
	(cd frontend-ui && EXPO_PUBLIC_ENV=development npx expo start --web > ../logs/frontend.log 2>&1) & \
	sleep 8 && echo "Servers should be ready!" && \
	echo "Frontend: http://localhost:8081" && \
	echo "Backend API: http://localhost:8000/api/" && \
	echo "View logs: make logs" && \
	echo "Stop servers: make stop" && \
	sleep 2 && make open && \
	wait

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
	pkill -f "python3 manage.py runserver" || true
	pkill -f "python manage.py runserver" || true
	pkill -f "python.*manage.py" || true
	pkill -f "expo start" || true
	@echo "Servers stopped"
