#!/bin/bash
# SAP Deployment Assistant V3 - Local Development Start
# Startet Backend + Frontend lokal (ohne Docker)

echo "╔═══════════════════════════════════════════════════╗"
echo "║   SAP Deployment Assistant V3 - Local Dev        ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Prüfe Ollama
echo "⏳ Prüfe Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama läuft auf localhost:11434"
else
    echo "❌ Ollama läuft nicht!"
    echo "   Zum Starten: ollama serve"
    exit 1
fi

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden!"
    exit 1
fi

# Prüfe Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js nicht gefunden!"
    exit 1
fi

echo ""
echo "🚀 Starte Backend..."
echo ""

# Backend starten (im Hintergrund)
cd backend
python3 main_v3.py &
BACKEND_PID=$!
cd ..

echo "Backend PID: $BACKEND_PID"

# Warte bis Backend bereit ist
echo "⏳ Warte auf Backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend läuft auf http://localhost:8000"
        break
    fi
    sleep 1
done

echo ""
echo "🚀 Starte Frontend..."
echo ""

# Frontend starten
cd frontend-react

# Installiere Dependencies (falls noch nicht geschehen)
if [ ! -d "node_modules" ]; then
    echo "📦 Installiere Frontend Dependencies..."
    npm install
fi

# Setze API URL
export VITE_API_URL=http://localhost:8000

# Starte Frontend
npm run dev &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"
cd ..

echo ""
echo "✅ Services gestartet!"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:5173"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Drücke Ctrl+C zum Beenden"
echo ""

# Warte auf Ctrl+C
trap "echo ''; echo '🛑 Stoppe Services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Halte Script am Laufen
wait
