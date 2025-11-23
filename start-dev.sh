#!/bin/bash
# SAP Deployment Assistant V3 - Local Development Start
# Startet Backend + Frontend lokal (ohne Docker)

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════╗"
echo "║   SAP Deployment Assistant V3 - Local Dev        ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Funktion: Cleanup alte Prozesse
cleanup_old_processes() {
    echo "🧹 Bereinige alte Prozesse..."

    # Backend-Prozesse killen (uvicorn, python main_v3.py)
    pkill -f "main_v3.py" 2>/dev/null || true
    pkill -f "uvicorn main_v3" 2>/dev/null || true

    # Frontend-Prozesse killen (vite, npm dev)
    pkill -f "vite" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true

    # Port 8000 (Backend) freigeben
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   Beende Prozess auf Port 8000..."
        kill -9 $(lsof -t -i:8000) 2>/dev/null || true
    fi

    # Port 5173/5174 (Frontend) freigeben
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   Beende Prozess auf Port 5173..."
        kill -9 $(lsof -t -i:5173) 2>/dev/null || true
    fi

    if lsof -Pi :5174 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   Beende Prozess auf Port 5174..."
        kill -9 $(lsof -t -i:5174) 2>/dev/null || true
    fi

    # Kurz warten damit Ports freigegeben werden
    sleep 2

    echo "✅ Cleanup abgeschlossen"
    echo ""
}

# Funktion: Prüfe Abhängigkeiten
check_dependencies() {
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

    # Prüfe lsof (für Port-Checks)
    if ! command -v lsof &> /dev/null; then
        echo "⚠️  lsof nicht gefunden - Port-Cleanup übersprungen"
    fi

    echo ""
}

# Funktion: Starte Backend
start_backend() {
    echo "🚀 Starte Backend..."
    echo ""

    # Erstelle data-Verzeichnis falls nicht vorhanden
    mkdir -p backend/data
    chmod 777 backend/data

    # Backend starten (im Hintergrund)
    cd backend
    python3 main_v3.py > ../backend.log 2>&1 &
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
        if [ $i -eq 30 ]; then
            echo "❌ Backend Start Timeout!"
            echo "   Letzte Logs:"
            tail -n 20 backend.log
            exit 1
        fi
        sleep 1
    done

    echo ""
}

# Funktion: Starte Frontend
start_frontend() {
    echo "🚀 Starte Frontend..."
    echo ""

    cd frontend-react

    # Installiere Dependencies (falls noch nicht geschehen)
    if [ ! -d "node_modules" ]; then
        echo "📦 Installiere Frontend Dependencies..."
        npm install
    fi

    # Setze API URL
    export VITE_API_URL=http://localhost:8000

    # Starte Frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!

    echo "Frontend PID: $FRONTEND_PID"
    cd ..

    # Warte kurz damit Vite startet
    sleep 3

    # Prüfe ob Frontend läuft
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        # Versuche Port zu erkennen (5173 oder 5174)
        if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            FRONTEND_PORT=5173
        elif lsof -Pi :5174 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            FRONTEND_PORT=5174
        else
            FRONTEND_PORT=5173
        fi
        echo "✅ Frontend läuft auf http://localhost:$FRONTEND_PORT"
    else
        echo "❌ Frontend Start fehlgeschlagen!"
        echo "   Letzte Logs:"
        tail -n 20 frontend.log
        exit 1
    fi

    echo ""
}

# Funktion: Cleanup bei Exit
cleanup_on_exit() {
    echo ""
    echo "🛑 Stoppe Services..."

    # Backend stoppen
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || true
    fi

    # Frontend stoppen
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # Sicherheitshalber alle Prozesse killen
    pkill -f "main_v3.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true

    echo "✅ Services gestoppt"
    exit 0
}

# Trap für Cleanup bei Ctrl+C oder Exit
trap cleanup_on_exit INT TERM EXIT

# === MAIN ===

# 1. Cleanup alte Prozesse
cleanup_old_processes

# 2. Prüfe Abhängigkeiten
check_dependencies

# 3. Starte Backend
start_backend

# 4. Starte Frontend
start_frontend

# 5. Zeige Info
echo "✅ Alle Services gestartet!"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:${FRONTEND_PORT:-5173}"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Drücke Ctrl+C zum Beenden"
echo ""

# Halte Script am Laufen
wait
