# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SAP Deployment Automation Assistant - A conversational AI agent that generates Terraform variable files (tfvars) for SAP deployments on Azure using the SAP Deployment Automation Framework (SDAF).

**Tech Stack:**
- Backend: FastAPI with LangChain + Ollama (llama3.1:8b)
- Frontend: Streamlit
- Database: SQLite for chat history persistence
- Deployment: Docker Compose

## Version 2.0 (Current)

The application has been **completely rewritten** in v2 to provide a true conversational AI experience:

### Key Improvements in V2:
- **Session-based architecture** (multi-user support, no global state)
- **6-prompt conversational flow** based on SDAF research
- **Natural language input** (LLM-driven parsing, case-insensitive)
- **180+ SDAF parameters** with sensible defaults
- **46 HANA sizing options** + 3 app tier profiles
- **Proper session management** UI with chat history sidebar
- **RESTful API** design

### File Structure:
- **Backend:** `backend/chat_agent_v2.py` (current), `backend/main_v2.py`
- **Frontend:** `frontend/chat_v2.py` (current)
- **Legacy:** `chat_agent_simple.py`, `chat.py` (deprecated, for reference only)
- **Documentation:** `SDAF_RESEARCH_REPORT.md`, `MIGRATION_GUIDE_V2.md`, `QUICKSTART_V2.md`

## Architecture

### Service Communication Flow

```
User → Streamlit Frontend (port 8501)
        ↓
    FastAPI Backend (port 8000)
        ↓
    Ollama LLM (host.docker.internal:11434)
```

### Core Components

**Backend (`backend/chat_agent_simple.py`):**
- Main application file with FastAPI endpoints
- Intent detection system with two paths:
  - **Fast-path**: Keyword-based responses for common questions (SAP SID, regions, sizing)
  - **Slow-path**: Async LLM invocation for unstructured/unknown questions
- Conversational flow: Environment → SAP System → TFVARS generation
- SQLite persistence with auto-initialization on startup
- Session management endpoints: `/save-chat`, `/load-chat`, `/list-sessions`

**Frontend (`frontend/chat.py`):**
- Streamlit chat interface
- Backend health checking with connection status indicator
- Auto-save functionality when TFVARS generation completes
- Session management UI in sidebar
- Dynamic TFVARS download with SID-based filename

**Templates (`templates/`):**
- `easy_defaults.yaml`: Default SAP deployment configuration values
- `sap.tfvars.j2`: Jinja2 template for Terraform variable file generation

**Data Persistence:**
- SQLite database at `/app/data/chat_history.db` (mounted volume)
- Stores conversation history, user answers, and generated TFVARS

### State Management

Backend uses a global `AgentState` class (MVP pattern) with:
- `messages`: List of (role, content) tuples
- `current_block`: Tracks conversation stage ("environment", "sap_system", "complete")
- `user_answers`: Dict storing parsed user inputs
- `tfvars_ready`: Boolean flag for generation completion
- `tfvars_content`: Final generated Terraform variables

## Development Commands

### Build and Run (V2)

```bash
# Start all services (builds if needed)
docker compose up --build

# Run in detached mode
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Rebuild after code changes
docker compose down && docker compose up --build
```

### Run Locally Without Docker (V2)

**Backend:**
```bash
cd backend
python3 main_v2.py
# Requires Ollama running on host at http://localhost:11434
```

**Frontend:**
```bash
cd frontend
export API_URL=http://localhost:8000
streamlit run chat_v2.py
```

### Testing

```bash
# Quick test script (requires backend running)
./test_v2.sh

# Or manual testing with curl
# See QUICKSTART_V2.md for detailed examples
```

### Access Points

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

### Local Development (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Ensure Ollama is running on host
python main.py
```

**Frontend:**
```bash
cd frontend
pip install -r requirements.txt
export API_URL=http://localhost:8000
streamlit run chat.py
```

### Database Access

```bash
# Access SQLite database directly
sqlite3 data/chat_history.db

# View all sessions
SELECT session_id, created_at FROM sessions;
```

## Key Implementation Details

### LLM Integration
- Model: `llama3.1:8b` via Ollama
- Connection: `http://host.docker.internal:11434` (Docker host gateway)
- Async mode enabled for non-blocking LLM calls
- In-memory caching enabled via LangChain

### Intent Detection Logic
Keywords trigger fast-path responses without LLM:
- "sap sid", "region", "sizing", "produkt" → Pre-defined informational responses
- "wer bist du", "was kannst du", "hilfe" → Help messages
- Other questions → Async LLM invocation with context-aware prompts

### TFVARS Generation Flow
1. Parse user inputs for Environment block (deployer, workload, region)
2. Parse SAP System block (SID, product, sizing)
3. Load defaults from `easy_defaults.yaml`
4. Merge user inputs with defaults
5. Apply sizing configuration (small/medium/large VM SKUs)
6. Render Jinja2 template → Terraform variable file

### Sizing Profiles (in chat_agent_simple.py:107-111)
- **small**: D4s_v3 (app), E16s_v3 (db), D2s_v3 (scs)
- **medium**: D8s_v3 (app), E32s_v3 (db), D4s_v3 (scs)
- **large**: D16s_v3 (app), E64s_v3 (db), D8s_v3 (scs)

## Important Files

- `backend/main.py`: Entry point (imports and runs FastAPI app)
- `backend/chat_agent_simple.py`: Core application logic
- `backend/chat_agent.py`: Alternative LangGraph-based implementation (not actively used)
- `docker-compose.yml`: Service orchestration with healthchecks and volume mounts
- `templates/sap.tfvars.j2`: Critical template - changes affect all generated configs

## Common Tasks

### Adding New Intent/Question Type
Edit `backend/chat_agent_simple.py` around line 141-204 (fast-path keyword detection):
```python
elif "new_keyword" in message_lower:
    reply = """Your response here"""
```

### Modifying TFVARS Template
Edit `templates/sap.tfvars.j2` - uses Jinja2 syntax with `{{ config.variable_name }}`

### Changing Default Values
Edit `templates/easy_defaults.yaml` - YAML format with key-value pairs

### Adding New Endpoints
Add FastAPI routes in `backend/chat_agent_simple.py` using `@app.post()` or `@app.get()` decorators

## Notes

- Backend requires Ollama running on host machine (not containerized)
- Database initialization happens automatically on backend startup (line 423-427)
- Frontend checks backend health before allowing interaction
- Data directory must be writable for SQLite operations
- Frontend auto-saves sessions when TFVARS generation completes
