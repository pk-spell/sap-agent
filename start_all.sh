#!/bin/bash
# Start Backend + Frontend - SAP Deployment Assistant V3

echo "🚀 Starting SAP Deployment Assistant V3..."
echo ""

# Check if we're in the right directory
if [ ! -f "start_backend_v3.sh" ]; then
    echo "❌ Error: Must run from sap-agent root directory"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check Ollama
echo "🔍 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo ""
    echo "Starting Ollama in background..."
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3

    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "❌ Failed to start Ollama"
        echo "Please run manually: ollama serve"
        exit 1
    fi
fi

echo "✅ Ollama is running"
echo ""

# Start Backend
echo "🚀 Starting Backend (http://localhost:8000)..."
cd backend
python3 main_v3.py > /tmp/backend_v3.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Check if backend started
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start"
    echo "Check logs: tail -f /tmp/backend_v3.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""

# Start Frontend
echo "🚀 Starting Frontend (http://localhost:5173)..."
cd frontend-react

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules not found. Running npm install..."
    npm install
fi

npm run dev > /tmp/frontend_v3.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   ✅ SAP Deployment Assistant V3 is RUNNING!             ║"
echo "║                                                           ║"
echo "║   Frontend: http://localhost:5173                        ║"
echo "║   Backend:  http://localhost:8000                        ║"
echo "║   API Docs: http://localhost:8000/docs                   ║"
echo "║                                                           ║"
echo "║   Press Ctrl+C to stop all services                      ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Logs:"
echo "  Backend:  tail -f /tmp/backend_v3.log"
echo "  Frontend: tail -f /tmp/frontend_v3.log"
echo "  Ollama:   tail -f /tmp/ollama.log"
echo ""

# Wait for user to stop
wait $FRONTEND_PID
