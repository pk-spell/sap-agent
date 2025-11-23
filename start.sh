#!/bin/bash
# SAP Deployment Assistant V3 - Startup Script
# Startet Backend + Frontend mit Docker Compose

echo "╔═══════════════════════════════════════════════════╗"
echo "║   SAP Deployment Assistant V3 - Docker Start     ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Prüfe ob Docker läuft
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker läuft nicht. Bitte starte Docker Desktop."
    exit 1
fi

# Prüfe ob Ollama läuft (optional, aber empfohlen)
echo "⏳ Prüfe Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama läuft auf localhost:11434"
else
    echo "⚠️  Ollama läuft nicht. Starte Ollama oder das Backend wird fehlschlagen."
    echo "   Zum Starten: ollama serve"
    echo ""
    read -p "Trotzdem fortfahren? (j/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starte Services..."
echo ""

# Stoppe alte Container (falls vorhanden)
docker compose down

# Baue und starte Services
docker compose up --build

echo ""
echo "✅ Services gestoppt."
