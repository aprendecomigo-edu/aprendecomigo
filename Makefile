.PHONY: dev backend frontend stop

backend:
	@echo "🚀 Starting Django backend server..."
	@if [ ! -d ".venv" ]; then echo "❌ Virtual environment not found at .venv"; exit 1; fi
	cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver

frontend:
	@echo "🌐 Starting Expo frontend server..."
	cd frontend-ui && EXPO_PUBLIC_ENV=development npm run web:dev

dev:
	@echo "🚀 Starting development servers..."
	@if [ ! -d ".venv" ]; then echo "❌ Virtual environment not found at .venv"; echo "💡 Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"; exit 1; fi
	@mkdir -p logs
	@echo "📝 Backend logs: logs/backend.log"
	@echo "📝 Frontend logs: logs/frontend.log"
	@echo "⏳ Please wait while servers start up..."
	(cd backend && source ../.venv/bin/activate && DJANGO_ENV=development python3 manage.py runserver > ../logs/backend.log 2>&1) & \
	(cd frontend-ui && EXPO_PUBLIC_ENV=development npx expo start --web > ../logs/frontend.log 2>&1) & \
	sleep 8 && echo "✅ Servers should be ready!" && \
	echo "🌐 Frontend: http://localhost:8081" && \
	echo "🔧 Backend API: http://localhost:8000/api/" && \
	echo "📋 View logs: tail -f logs/backend.log logs/frontend.log" && \
	echo "🛑 Stop servers: make stop" && \
	wait

stop:
	@echo "🛑 Stopping development servers..."
	pkill -f "python3 manage.py runserver" || true
	pkill -f "python manage.py runserver" || true
	pkill -f "python.*manage.py" || true
	pkill -f "expo start" || true
	@echo "✅ Servers stopped"
