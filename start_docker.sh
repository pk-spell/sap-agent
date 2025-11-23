#!/bin/bash
# Start SAP Deployment Assistant V3 - Docker Edition

echo "🐳 Starting SAP Deployment Assistant V3 with Docker..."
echo ""

# Check if Ollama is running on host
echo "🔍 Checking Ollama on host..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama is not running!"
    echo ""
    echo "Please start Ollama first:"
    echo "  ollama serve"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Build and start containers
echo "🚀 Building and starting containers..."
docker compose -f docker-compose.v3.yml up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check backend health
echo ""
echo "🔍 Checking backend..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend is starting..."
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   ✅ SAP Deployment Assistant V3 (Docker)                ║"
echo "║                                                           ║"
echo "║   Frontend: http://localhost:5173                        ║"
echo "║   Backend:  http://localhost:8000                        ║"
echo "║   API Docs: http://localhost:8000/docs                   ║"
echo "║                                                           ║"
echo "║   Commands:                                              ║"
echo "║   - docker compose -f docker-compose.v3.yml logs -f      ║"
echo "║   - docker compose -f docker-compose.v3.yml down         ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
