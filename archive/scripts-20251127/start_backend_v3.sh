#!/bin/bash
# Start Backend V3 - Local Edition
# With LLM-Factory (austauschbare LLMs!)

echo "🚀 Starting SAP Deployment Assistant V3..."
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║   SAP Deployment Assistant V3 - Local Edition    ║"
echo "║                                                   ║"
echo "║   Backend: FastAPI + Agent V3                    ║"
echo "║   LLM: Ollama (austauschbar!)                    ║"
echo "║   Kosten: €0                                     ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Check if Ollama is running
echo "🔍 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo ""
    echo "Please start Ollama first:"
    echo "  ollama serve"
    echo ""
    echo "Or in another terminal:"
    echo "  ollama serve &"
    echo ""
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Check if qwen2.5:7b is available
echo "🔍 Checking qwen2.5:7b model..."
if ollama list | grep -q "qwen2.5:7b"; then
    echo "✅ qwen2.5:7b model is available"
else
    echo "⚠️  qwen2.5:7b not found"
    echo ""
    echo "Downloading qwen2.5:7b (4.7 GB)..."
    ollama pull qwen2.5:7b
fi
echo ""

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
cd backend

if ! python3 -c "import langchain_ollama" 2>/dev/null; then
    echo "⚠️  Dependencies missing!"
    echo ""
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "✅ Dependencies installed"
echo ""

# Start FastAPI
echo "🚀 Starting FastAPI server..."
echo ""
echo "Backend will be available at:"
echo "  http://localhost:8000"
echo ""
echo "API Documentation:"
echo "  http://localhost:8000/docs"
echo ""
echo "Health Check:"
echo "  http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 main_v3.py
