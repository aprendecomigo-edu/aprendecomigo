# 🚀 QA Testing with Enhanced Makefile Commands

This guide covers the new simplified development server management for QA testing.

## 📋 Quick Reference

| Command | Description | Use Case |
|---------|-------------|----------|
| `make dev` | Start both servers | Standard QA testing |
| `make dev-open` | Start servers + open browser | Quick testing with auto-browser |
| `make stop` | Stop all servers | Clean shutdown |
| `make logs` | View recent logs | Debugging issues |
| `make open` | Open browser manually | Access frontend after startup |

## 🎯 Basic QA Workflow

### **Step 1: Start Development Environment**
```bash
cd /path/to/aprendecomigo
source .venv/bin/activate  # Only needed once per terminal session
make dev
```

**Expected Output:**
```
🚀 Starting development servers...
📝 Backend logs: logs/backend.log
📝 Frontend logs: logs/frontend.log
⏳ Please wait while servers start up...
✅ Servers should be ready!
🌐 Frontend: http://localhost:8081
🔧 Backend API: http://localhost:8000/api/
📋 View logs: make logs
🛑 Stop servers: make stop
🌐 Open browser: make open
```

### **Step 2: Perform QA Testing**
- Frontend is available at: http://localhost:8081
- Backend API at: http://localhost:8000/api/
- Use `make logs` to debug any issues

### **Step 3: Clean Shutdown**
```bash
make stop
```

## 🔧 Troubleshooting

### **Virtual Environment Issues**
If you see: `❌ Virtual environment not found at .venv`

**Solution:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### **Port Already in Use**
If backend shows "port already in use":

**Solution:**
```bash
make stop  # Standard cleanup
# If that doesn't work:
pkill -9 -f "manage.py runserver"
```

### **Debugging Server Issues**
```bash
make logs  # View recent logs
tail -f logs/backend.log logs/frontend.log  # Live log viewing
cat logs/backend.log  # Full backend log
cat logs/frontend.log  # Full frontend log
```

## 🎯 Advanced Usage

### **Auto-Browser Opening**
For quick testing sessions:
```bash
make dev-open  # Automatically opens browser to frontend
```

### **Individual Services**
```bash
make backend   # Start only Django backend
make frontend  # Start only Expo frontend
```

## ⚡ Quick Start for New QA Testers

1. **One-time setup:**
   ```bash
   git clone <repository>
   cd aprendecomigo
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   cd frontend-ui && npm install && cd ..
   ```

2. **Every testing session:**
   ```bash
   source .venv/bin/activate
   make dev-open
   # Start testing at http://localhost:8081
   # When done: make stop
   ```

## 📝 Legacy vs New Commands

### **Old Way (Don't use anymore):**
```bash
# ❌ OLD - Complex and error-prone
cd backend
export DJANGO_ENV=development
python manage.py runserver 8000 > /tmp/django_server.log 2>&1 &
cd ../frontend-ui
export EXPO_PUBLIC_ENV=development
npm run web &
```

### **New Way (Use this):**
```bash
# ✅ NEW - Simple and reliable
make dev
```

## 🎉 Benefits

- **200+ lines of commands** → **Single command**
- **Automatic logging** to `logs/` directory
- **Environment variables** set automatically
- **Cross-platform compatibility**
- **Built-in error checking**
- **Professional user feedback**