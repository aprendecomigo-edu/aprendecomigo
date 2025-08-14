.PHONY: dev dev-web dev-ios dev-android stop logs test test-watch test-coverage lint format clean install setup help build-web build-ios build-android

# Development server commands
dev:
	@echo "Starting Expo development server..."
	@mkdir -p logs
	@TIMESTAMP=$$(date +"%Y%m%d-%H%M%S"); \
	echo "Stopping any existing servers on port 8081..."; \
	lsof -ti:8081 | xargs kill -9 2>/dev/null || true; \
	sleep 1; \
	echo "Starting Expo..."; \
	(EXPO_PUBLIC_ENV=development npx expo start > logs/expo-$$TIMESTAMP.log 2>&1) & \
	echo $$! > logs/expo.pid; \
	sleep 5; \
	echo "Expo Dev Server ready!"; \
	echo "  › Metro: http://localhost:8081"; \
	echo "  › Web: Press 'w' in terminal"; \
	echo "  › iOS: Press 'i' in terminal"; \
	echo "  › Android: Press 'a' in terminal"; \
	echo "View logs: make logs"; \
	echo "Stop server: make stop"
	@trap 'make stop' INT; while true; do sleep 1; done

dev-web:
	@echo "Starting Expo for web..."
	@mkdir -p logs
	@TIMESTAMP=$$(date +"%Y%m%d-%H%M%S"); \
	lsof -ti:8081 | xargs kill -9 2>/dev/null || true; \
	sleep 1; \
	(EXPO_PUBLIC_ENV=development npx expo start --web > logs/expo-web-$$TIMESTAMP.log 2>&1) & \
	echo $$! > logs/expo.pid; \
	sleep 5; \
	echo "Web app ready at http://localhost:8081"
	@trap 'make stop' INT; while true; do sleep 1; done

dev-ios:
	@echo "Starting Expo for iOS..."
	EXPO_PUBLIC_ENV=development npx expo start --ios

dev-android:
	@echo "Starting Expo for Android..."
	EXPO_PUBLIC_ENV=development npx expo start --android

stop:
	@echo "Stopping Expo server..."
	@if [ -f "logs/expo.pid" ]; then \
		kill -TERM $$(cat logs/expo.pid) 2>/dev/null || true; \
		rm -f logs/expo.pid; \
	fi
	@lsof -ti:8081 | xargs kill -9 2>/dev/null || true
	@lsof -ti:19000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:19001 | xargs kill -9 2>/dev/null || true
	@pkill -f "expo start" || true
	@pkill -f "react-native" || true
	@echo "Server stopped"

logs:
	@echo "Expo Server Logs"
	@echo "================"
	@if [ ! -d "logs" ]; then echo "No logs directory found. Run 'make dev' first."; exit 1; fi
	@LATEST_LOG=$$(ls -t logs/expo*.log 2>/dev/null | head -1); \
	if [ -z "$$LATEST_LOG" ]; then \
		echo "No log files found. Make sure server is running."; exit 1; \
	fi; \
	echo "Latest log: $$LATEST_LOG"; \
	echo "--------------------------------"; \
	tail -20 "$$LATEST_LOG"; \
	echo ""; \
	echo "For live logs: tail -f $$LATEST_LOG"

# Testing commands
test:
	@echo "Running tests..."
	npm test -- --watchAll=false

test-watch:
	@echo "Running tests in watch mode..."
	npm test

test-coverage:
	@echo "Running tests with coverage..."
	npm test -- --coverage --watchAll=false

# Code quality
lint:
	@echo "Running ESLint..."
	npx eslint . --ext .js,.jsx,.ts,.tsx

format:
	@echo "Formatting code with Prettier..."
	npx prettier --write "**/*.{js,jsx,ts,tsx,json,css,md}"

# Build commands
build-web:
	@echo "Building for web..."
	EXPO_PUBLIC_ENV=production npx expo export --platform web

build-ios:
	@echo "Building for iOS..."
	eas build --platform ios

build-android:
	@echo "Building for Android..."
	eas build --platform android

# Utility commands
clean:
	@echo "Cleaning project..."
	@rm -rf node_modules
	@rm -rf .expo
	@rm -rf dist
	@rm -rf web-build
	@rm -rf ios/build
	@rm -rf android/build
	@rm -rf logs
	@echo "Clean complete!"

install:
	@echo "Installing dependencies..."
	npm install
	@echo "Dependencies installed!"

setup: install
	@echo "Frontend setup complete!"
	@echo "Run 'make dev' to start the development server"

# Expo specific commands
expo-doctor:
	@echo "Running Expo Doctor..."
	npx expo-doctor

expo-upgrade:
	@echo "Upgrading Expo SDK..."
	npx expo upgrade

prebuild:
	@echo "Running Expo prebuild..."
	npx expo prebuild --clean

clear-cache:
	@echo "Clearing Metro bundler cache..."
	npx expo start --clear
	@echo "Clearing React Native cache..."
	npx react-native start --reset-cache || true
	@echo "Cache cleared!"

# Help
help:
	@echo "Available commands:"
	@echo "  make dev           - Start Expo development server"
	@echo "  make dev-web       - Start Expo for web only"
	@echo "  make dev-ios       - Start Expo for iOS"
	@echo "  make dev-android   - Start Expo for Android"
	@echo "  make stop          - Stop the server"
	@echo "  make logs          - View server logs"
	@echo "  make test          - Run tests"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo "  make test-coverage - Run tests with coverage"
	@echo "  make lint          - Run ESLint"
	@echo "  make format        - Format code with Prettier"
	@echo "  make build-web     - Build for web"
	@echo "  make build-ios     - Build for iOS (requires EAS)"
	@echo "  make build-android - Build for Android (requires EAS)"
	@echo "  make clean         - Clean all build artifacts"
	@echo "  make install       - Install dependencies"
	@echo "  make setup         - Complete setup"
	@echo "  make expo-doctor   - Check project health"
	@echo "  make clear-cache   - Clear all caches"