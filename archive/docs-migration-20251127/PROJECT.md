# SAP Deployment Automation Assistant

**Version:** 2.0 (Refactored)
**Status:** Production-Ready (Frontend), Partially Refactored (Backend)
**Last Updated:** 2025-11-20

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Current Status](#current-status)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Development Workflow](#development-workflow)
- [Known Issues & TODOs](#known-issues--todos)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Key Features](#key-features)
- [Configuration](#configuration)

---

## 📖 Project Overview

### What is this?

An **AI-powered conversational assistant** that generates production-ready Terraform variable files (tfvars) for SAP deployments on Azure using the SAP Deployment Automation Framework (SDAF).

### Problem it solves

- Manual tfvars creation is error-prone and time-consuming
- SDAF has 180+ configuration parameters
- Users need to know exact Azure region codes, VM sizes, and SDAF conventions
- No user-friendly interface exists for SDAF configuration

### Solution

A **chat-based interface** with:
- Natural language input processing
- **Interactive forms** for critical configuration steps (NEW in v2!)
- Intelligent defaults for 180+ SDAF parameters
- 46 HANA sizing options (Demo to 4TB+ production)
- Session management for multiple configurations
- Auto-configuration for common scenarios (Demo/Test systems)

---

## 🏗️ Architecture

### High-Level Flow

```
User (Browser)
    ↓
Streamlit Frontend (port 8501)
    ↓ HTTP/REST
FastAPI Backend (port 8000)
    ↓
├── SQLite (session persistence)
├── Ollama LLM (llama3.1:8b for parsing)
└── Jinja2 Templates (tfvars generation)
```

### Communication Pattern

1. **Frontend** → API Client → **Backend**
2. **Backend** → LLM for natural language parsing
3. **Backend** → Database for session persistence
4. **Backend** → Templates for tfvars generation
5. **Backend** → Frontend with response + current_prompt state

### Key Design Decisions

- **Hybrid Parsing:** Regex first (fast), fallback to LLM (flexible)
- **Stateful Sessions:** Each chat maintains conversation context
- **Progressive Questioning:** 6-step conversation flow (Prompts 0-5)
- **Smart Defaults:** User only specifies what matters, rest auto-filled
- **Interactive Widgets:** Forms for Prompt 0 (Environment) & Prompt 1 (SAP System)

---

## 🎯 Current Status

### ✅ Completed (v2.0)

**Frontend:**
- ✅ **Fully refactored** into modular components (972 → 313 lines in main file)
- ✅ Interactive widgets for Environment & SAP System configuration
- ✅ Landing page with "Try Now" CTA
- ✅ Session management (create, switch, delete)
- ✅ Chat history persistence
- ✅ Download tfvars with auto-generated filename
- ✅ Responsive UI with Elex Clerics tech theme
- ✅ Multi-page Streamlit app structure

**Backend:**
- ✅ 6-prompt conversational flow
- ✅ Context-aware parsing (fixes "SAP01" loop bug)
- ✅ Auto-configuration for Demo/Test sizing (skips Prompt 3)
- ✅ SQLite persistence
- ✅ RESTful API design
- ✅ Ollama LLM integration (llama3.1:8b)
- ✅ Jinja2 template-based tfvars generation
- ✅ **Partially refactored** (config, models, database extracted)

### 🔄 In Progress

**Backend Refactoring:**
- ⏳ Parser modules (environment, sap_system, sizing, architecture, network, os)
- ⏳ Prompt messages module
- ⏳ TFVARS generator module
- ⏳ Clean up main_v2.py to use modular imports

### 🐛 Known Issues

1. **Backend Parsing Loop (FIXED!):** "SAP01" alone caused infinite loop → Now context-aware
2. **HA Auto-Configuration (FIXED!):** Demo sizing now auto-sets standalone, no-HA, skips Prompt 3
3. **Widget Display (FIXED!):** Widgets now correctly shown for Prompt 0 & 1
4. **Backend Code Monolith:** chat_agent_v2.py still has 1606 lines → Refactoring in progress

---

## 🛠️ Tech Stack

### Frontend
- **Streamlit** 1.31.0 - Multi-page web app framework
- **Requests** 2.31.0 - HTTP client for backend API
- **Python** 3.11

### Backend
- **FastAPI** - Async REST API framework
- **LangChain** - LLM orchestration
- **Ollama** - Local LLM runtime (llama3.1:8b model)
- **SQLite** - Session persistence
- **Jinja2** - Template engine for tfvars
- **PyYAML** - Config file parsing
- **Python** 3.11

### Infrastructure
- **Docker Compose** - Container orchestration
- **Uvicorn** - ASGI server
- **SQLite** - Embedded database

---

## 📁 Project Structure

### Frontend (Refactored ✅)

```
frontend/
├── Home.py                          # Landing page with "Try Now" button
├── pages/
│   └── chat.py                      # Main chat UI (313 lines)
├── components/                      # ⬅️ MODULAR COMPONENTS
│   ├── __init__.py
│   ├── widgets.py                   # Interactive forms (Environment, SAP System)
│   └── sidebar.py                   # Session management UI
├── api/
│   ├── __init__.py
│   └── client.py                    # Backend API client (BackendClient class)
├── utils/
│   ├── __init__.py
│   └── helpers.py                   # SID extraction, formatting
├── _old_v1/                         # Backup of v1 code
│   ├── chat.py                      # Original v1 (deprecated)
│   └── chat_v2.py                   # Pre-refactor version
├── requirements.txt
└── Dockerfile
```

### Backend (Partially Refactored 🔄)

```
backend/
├── main_v2.py                       # FastAPI app entry point (runs uvicorn)
├── chat_agent_v2.py                 # ⚠️ MONOLITH (1606 lines) - NEEDS REFACTORING
├── config.py                        # ✅ Configuration, LLM setup, constants
├── models/                          # ✅ Data models
│   ├── __init__.py
│   └── session.py                   # ChatSession dataclass
├── database/                        # ✅ Database layer
│   ├── __init__.py
│   └── operations.py                # CRUD operations for sessions
├── utils/                           # ✅ Utilities
│   ├── __init__.py
│   └── helpers.py                   # Region validation, session ID generation
├── parsers/                         # ❌ TODO: Extract from chat_agent_v2.py
│   └── __init__.py                  # (environment, sap_system, sizing, architecture, network, os)
├── prompts/                         # ❌ TODO: Extract from chat_agent_v2.py
│   └── __init__.py                  # (6 prompt messages)
├── tfvars/                          # ❌ TODO: Extract from chat_agent_v2.py
│   └── __init__.py                  # (generator.py with Jinja2 logic)
├── _old_v1/                         # Old deprecated files
│   ├── chat_agent.py                # LangGraph version (not used)
│   └── chat_agent_simple.py         # Original MVP (deprecated)
├── requirements.txt
└── Dockerfile
```

### Shared Resources

```
templates/
├── easy_defaults.yaml               # Default SDAF parameter values (180+ params)
└── sap.tfvars.j2                   # Jinja2 template for tfvars generation

data/
└── chat_sessions_v2.db              # SQLite database (auto-created)

docker-compose.yml                   # Service orchestration
```

---

## 🚀 Setup & Installation

### Prerequisites

1. **Docker & Docker Compose** installed
2. **Ollama** running on host machine with `llama3.1:8b` model pulled
3. **Host Ollama accessible** at `http://host.docker.internal:11434`

### Quick Start

```bash
# 1. Clone/navigate to project
cd /home/kuschi/sap-agent

# 2. Ensure Ollama is running on host
ollama run llama3.1:8b  # Pull model if needed

# 3. Start services
docker compose up --build

# 4. Access application
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Rebuild After Code Changes

```bash
docker compose down
docker compose up --build
```

### Run Without Docker (Development)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main_v2.py
# Requires Ollama at http://localhost:11434
```

**Frontend:**
```bash
cd frontend
pip install -r requirements.txt
export API_URL=http://localhost:8000
streamlit run Home.py
```

---

## 💻 Development Workflow

### Making Changes

1. **Frontend changes:** Edit files in `frontend/` → Restart frontend container
2. **Backend changes:** Edit files in `backend/` → Restart backend container
3. **Template changes:** Edit `templates/*.j2` or `*.yaml` → Restart backend

### Testing Flow

```bash
# 1. Start fresh session
docker compose down
docker compose up --build

# 2. Navigate to http://localhost:8501
# 3. Click "🚀 TRY NOW"
# 4. Test conversation flow:
#    - Prompt 0: Use Environment widget (DEV, westeurope, SAP01)
#    - Prompt 1: Use SAP System widget (X00, HDB, HANA)
#    - Prompt 2: Type "Demo" → Should auto-configure & skip Prompt 3
#    - Prompt 4: Network config
#    - Prompt 5: OS selection
#    - Prompt 6: Confirmation → Download tfvars
```

### Common Development Tasks

**Add new widget:**
1. Edit `frontend/components/widgets.py`
2. Add render function
3. Import in `frontend/pages/chat.py`
4. Call in appropriate prompt condition

**Change prompt message:**
1. Currently in `backend/chat_agent_v2.py` (lines ~1050-1150)
2. TODO: Will be in `backend/prompts/messages.py` after refactoring

**Modify SDAF defaults:**
1. Edit `templates/easy_defaults.yaml`
2. Restart backend

**Change tfvars template:**
1. Edit `templates/sap.tfvars.j2`
2. Restart backend

---

## 🐛 Known Issues & TODOs

### Critical Issues (All Fixed! ✅)

- ✅ **Widget Display Issue:** Widgets weren't showing → Fixed by updating `pages/chat.py`
- ✅ **Parsing Loop Bug:** "SAP01" caused infinite loop → Fixed with context-aware parsing
- ✅ **Demo Auto-Config:** Demo sizing asked for HA → Now auto-sets standalone, no-HA

### Code Quality Issues

- ⚠️ **Backend Monolith:** `chat_agent_v2.py` has 1606 lines
  - **Status:** Partially refactored (config, models, database extracted)
  - **TODO:** Extract parsers, prompts, tfvars modules
  - **Impact:** Low (functional, just not maintainable)

### Future Enhancements

1. **More Interactive Widgets:**
   - Prompt 2 (Sizing): Dropdown for database sizes
   - Prompt 3 (Architecture): Radio buttons for deployment type
   - Prompt 4 (Network): Subnet calculator widget

2. **Validation Improvements:**
   - Real-time SID validation in widgets
   - Azure region availability check
   - VM SKU compatibility validation

3. **Backend Refactoring:**
   - Complete parser module extraction
   - Separate prompt messages
   - Modular TFVARS generator
   - Clean main_v2.py (endpoints only)

4. **Testing:**
   - Unit tests for parsers
   - Integration tests for API endpoints
   - E2E tests for full conversation flow

5. **UX Enhancements:**
   - Edit previous answers
   - Preview tfvars during conversation
   - Export conversation as PDF
   - Share session via URL

---

## 📚 API Documentation

### Base URL
`http://localhost:8000`

### Endpoints

#### Health Check
```http
GET /health
Response: {"status": "healthy"}
```

#### Create New Session
```http
POST /sessions/new
Response: {
  "session_id": "abc12345",
  "message": "Welcome! Let's configure...",
  "current_prompt": 0
}
```

#### Send Message
```http
POST /sessions/{session_id}/chat
Body: {"message": "DEV, westeurope, SAP01"}
Response: {
  "message": "Got it! Environment: DEV...",
  "current_prompt": 1,
  "tfvars_ready": false
}
```

#### Get Session
```http
GET /sessions/{session_id}
Response: {
  "session_id": "abc12345",
  "messages": [...],
  "current_prompt": 2,
  "tfvars_ready": false,
  "tfvars_content": ""
}
```

#### List All Sessions
```http
GET /sessions
Response: {
  "sessions": [
    {
      "session_id": "abc12345",
      "title": "SAP X00 - DEV - westeurope",
      "current_prompt": 3,
      "tfvars_ready": false,
      "created_at": "2025-11-20T12:00:00",
      "updated_at": "2025-11-20T12:05:00",
      "message_count": 6
    }
  ]
}
```

#### Delete Session
```http
DELETE /sessions/{session_id}
Response: {"success": true}
```

---

## 🗄️ Database Schema

### Tables

**chat_sessions**
```sql
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    title TEXT,
    current_prompt INTEGER DEFAULT 0,
    user_data TEXT,              -- JSON string of collected parameters
    tfvars_content TEXT,
    tfvars_ready BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**chat_messages**
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,          -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
```

---

## ✨ Key Features

### 1. Conversational Flow (6 Prompts)

**Prompt 0: Environment Identity**
- Environment type (DEV/PROD/QA/etc.)
- Azure region
- Network logical name
- **Widget:** Interactive form with dropdowns

**Prompt 1: SAP System Identity**
- SAP Application SID (3 chars)
- Database SID (3 chars)
- Database platform (HANA/DB2/ORACLE/etc.)
- **Widget:** Interactive form with text inputs + dropdown

**Prompt 2: System Sizing**
- Database size (Demo/S4Demo/192GB/256GB/...4TB)
- App tier sizing (Optimized/Production)
- Purpose (development/production)
- **Auto-Config:** "Demo" → Skips Prompt 3, sets standalone + no-HA

**Prompt 3: Architecture Pattern** (Auto-skipped for Demo)
- Deployment type (standalone/distributed)
- High availability (yes/no)
- Application server count

**Prompt 4: Network Configuration**
- Network ARM ID
- Subnet info
- Use existing/create new

**Prompt 5: Operating System**
- OS type (Linux/Windows)
- OS image details

**Prompt 6: Final Confirmation**
- Review configuration
- Generate tfvars

### 2. Intelligent Parsing

**Hybrid Approach:**
1. **Regex First:** Fast pattern matching for common formats
   - "DEV, westeurope, SAP01" → Instant parsing
   - "X00, HDB, HANA" → Instant parsing
2. **LLM Fallback:** Natural language understanding
   - "I want dev environment in west europe called SAP01"
   - 15-second timeout on LLM calls

**Context-Aware:**
- Tracks what's already collected
- Single word interpreted based on context
- Example: "SAP01" recognized as network_name if env+region already set

### 3. Smart Defaults

**Easy Defaults (180+ parameters):**
- Loaded from `templates/easy_defaults.yaml`
- User only specifies critical values
- Rest auto-filled with best practices

**Auto-Configuration:**
- Demo/Test sizing → Standalone, no-HA
- Production sizing → Prompts for distributed + HA
- Region codes → Auto-converted (westeurope → WEEU)

### 4. Session Management

- Create unlimited sessions
- Switch between sessions
- Delete old sessions
- Auto-save on tfvars generation
- Persistent across container restarts

---

## ⚙️ Configuration

### Environment Variables

**Frontend:**
- `API_URL`: Backend URL (default: `http://backend:8000`)

**Backend:**
- `OLLAMA_HOST`: Ollama URL (default: `http://host.docker.internal:11434`)

### Ollama Configuration

**Model:** `llama3.1:8b`
**Temperature:** 0.3 (low for consistent parsing)
**Timeout:** 15 seconds per LLM call

### Azure Region Support

Currently supports 35+ Azure regions (see `backend/config.py` for full list)

---

## 🎨 UI Theme

**Elex Clerics Inspired Tech Theme:**
- Dark gradient background (#0a0e1a)
- Cyan accent (#00d9ff) with glow effects
- Orbitron font for headings
- Rajdhani font for body text
- Animated chat messages (slide-in)
- Gradient buttons with hover effects

---

## 📝 Notes for AI Coding Assistants

### When working on this project:

1. **Frontend changes:** All modular components are in `frontend/components/`, `frontend/api/`, `frontend/utils/`
2. **Backend changes:** Currently `chat_agent_v2.py` is monolithic (1606 lines) - see refactoring TODO
3. **New widgets:** Add to `frontend/components/widgets.py` following existing pattern
4. **API changes:** Edit `backend/chat_agent_v2.py` endpoints section (lines ~1400-1600)
5. **Database:** Use functions in `backend/database/operations.py` (already extracted)

### Architecture Principles:

- **Frontend:** Component-based, API client abstraction, no business logic
- **Backend:** RESTful, stateless endpoints, session state in DB
- **Parsing:** Regex first (fast), LLM fallback (flexible)
- **Defaults:** User provides minimum, system infers maximum

### Code Style:

- Type hints everywhere
- Docstrings for all functions
- Logging with emojis (✅ ❌ ⏱️ ℹ️)
- Clear separation of concerns

---

## 🚨 Emergency Contacts

**Project Location:** `/home/kuschi/sap-agent`
**Database:** `/home/kuschi/sap-agent/data/chat_sessions_v2.db`
**Templates:** `/home/kuschi/sap-agent/templates/`

**If backend won't start:**
1. Check Ollama is running: `ollama list`
2. Check database permissions: `ls -la data/`
3. Check logs: `docker logs sap-agent-backend`

**If frontend won't start:**
1. Check backend is healthy: `curl http://localhost:8000/health`
2. Check logs: `docker logs sap-agent-frontend`

---

## 📄 License & Credits

**Built with:** Claude Code (Anthropic)
**Author:** Generated via AI-assisted development
**Date:** November 2025

**Technologies:**
- FastAPI, Streamlit, LangChain, Ollama
- SDAF (SAP Deployment Automation Framework)
- Docker, SQLite, Jinja2

---

**Last Updated:** 2025-11-20
**Status:** Production-Ready (Frontend), Active Development (Backend Refactoring)
