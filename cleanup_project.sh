#!/bin/bash
# Project Cleanup Script - SAP Agent
# Aufräumen vor React/Azure AI Migration

set -e

echo "🧹 Starting Project Cleanup..."

# 1. Create new folder structure
echo "📁 Creating new folder structure..."
mkdir -p docs/archive
mkdir -p docs/migration-plans
mkdir -p _archive/backend
mkdir -p _archive/frontend

# 2. Move old MD files to docs
echo "📄 Moving documentation files..."

# Keep in root: Only essential files
# - CLAUDE.md (for AI context)
# - README.md (project overview)
# - PROJECT.md (current state)

# Move to docs/archive (old summaries, not needed anymore)
mv DELIVERY_SUMMARY.md docs/archive/ 2>/dev/null || true
mv IMPLEMENTATION_SUMMARY.md docs/archive/ 2>/dev/null || true
mv IMPLEMENTATION_SUMMARY_DE.md docs/archive/ 2>/dev/null || true
mv FIXES_COMPLETE.md docs/archive/ 2>/dev/null || true
mv REFACTORING_COMPLETE.md docs/archive/ 2>/dev/null || true
mv STRICT_VALIDATION_COMPLETE.md docs/archive/ 2>/dev/null || true
mv VALIDATION_COMPLETE.md docs/archive/ 2>/dev/null || true
mv STREAMLIT_EXPLANATION.md docs/archive/ 2>/dev/null || true
mv OPTION_C_SUMMARY.md docs/archive/ 2>/dev/null || true

# Move to docs/migration-plans (migration docs)
mv AZURE_AI_MIGRATION_PLAN.md docs/migration-plans/ 2>/dev/null || true
mv REACT_QUICKSTART.md docs/migration-plans/ 2>/dev/null || true
mv MIGRATION_GUIDE_V2.md docs/migration-plans/ 2>/dev/null || true

# Move user guides to docs/
mv QUICKSTART_V2.md docs/ 2>/dev/null || true
mv USER_GUIDE.md docs/ 2>/dev/null || true
mv SUGGESTIONS.md docs/ 2>/dev/null || true
mv IMPROVEMENTS.md docs/ 2>/dev/null || true
mv KNOWN_ISSUES_TODO.md docs/ 2>/dev/null || true

# Keep SDAF_RESEARCH_REPORT.md - needed for RAG/context
mv SDAF_RESEARCH_REPORT.md docs/ 2>/dev/null || true

# 3. Archive old backend files
echo "🗄️  Archiving old backend code..."
mv backend/chat_agent.py _archive/backend/ 2>/dev/null || true
mv backend/chat_agent_simple.py _archive/backend/ 2>/dev/null || true
mv backend/main.py _archive/backend/ 2>/dev/null || true
mv backend/_old _archive/backend/ 2>/dev/null || true

# Keep: chat_agent_v2.py, main_v2.py, all parsers, validators, tfvars

# 4. Archive old frontend files
echo "🗄️  Archiving old frontend code..."
mv frontend/_old_v1 _archive/frontend/ 2>/dev/null || true
mv frontend/Home.py _archive/frontend/ 2>/dev/null || true

# Keep: pages/chat.py, components/, api/, utils/

# 5. Create index files for docs
cat > docs/README.md << 'EOF'
# Documentation Index

## Current Documentation
- [SDAF Research Report](./SDAF_RESEARCH_REPORT.md) - RAG knowledge base
- [Quickstart V2](./QUICKSTART_V2.md) - How to run current version
- [User Guide](./USER_GUIDE.md) - End-user documentation

## Migration Plans
- [Azure AI Migration Plan](./migration-plans/AZURE_AI_MIGRATION_PLAN.md) - **Main migration doc**
- [React Quickstart](./migration-plans/REACT_QUICKSTART.md) - React setup guide
- [Migration Guide V2](./migration-plans/MIGRATION_GUIDE_V2.md) - V2 migration notes

## Archive (Historical)
Old implementation summaries and completed tasks are in [archive/](./archive/).
EOF

# 6. Create cleanup summary
cat > docs/CLEANUP_SUMMARY.md << 'EOF'
# Project Cleanup Summary

## What was cleaned up?

### Archived Files (not deleted, moved to `_archive/`)
**Backend:**
- `chat_agent.py` - Old LangGraph version
- `chat_agent_simple.py` - Simple version (pre-v2)
- `main.py` - Old entry point
- `_old/` - Old monolithic version

**Frontend:**
- `_old_v1/` - Version 1 files
- `Home.py` - Old homepage

### Documentation moved to `docs/`
All `.md` files are now organized:
- Root: Only `CLAUDE.md`, `README.md`, `PROJECT.md`
- `docs/` - Active documentation
- `docs/migration-plans/` - Migration guides
- `docs/archive/` - Historical summaries

## Current Active Files

### Backend (V2)
- `backend/main_v2.py` - Current entry point
- `backend/chat_agent_v2.py` - Current agent
- `backend/parsers/` - All parsers (KEEP!)
- `backend/utils/` - Validators, helpers (KEEP!)
- `backend/tfvars/` - Generator (KEEP!)
- `backend/database/` - SQLite operations
- `backend/models/` - Data models

### Frontend (V2)
- `frontend/pages/chat.py` - Main chat UI
- `frontend/components/` - UI components
- `frontend/api/` - API client
- `frontend/utils/` - Helper functions

## Next Steps: Migration to React + Azure AI

See [docs/migration-plans/AZURE_AI_MIGRATION_PLAN.md](./migration-plans/AZURE_AI_MIGRATION_PLAN.md)
EOF

# 7. Update README.md with new structure
cat > README.md << 'EOF'
# SAP Deployment Automation Assistant

Conversational AI agent that generates Terraform variable files (tfvars) for SAP deployments on Azure using the SAP Deployment Automation Framework (SDAF).

## Current Version: V2 (Streamlit + FastAPI)

**Tech Stack:**
- Backend: FastAPI + LangChain + Ollama
- Frontend: Streamlit
- Database: SQLite

## Quick Start

```bash
# Start all services
docker compose up --build

# Access frontend
open http://localhost:8501
```

For detailed instructions, see [docs/QUICKSTART_V2.md](./docs/QUICKSTART_V2.md)

## Documentation

- **[docs/](./docs/)** - All documentation
- **[docs/migration-plans/](./docs/migration-plans/)** - Migration to React + Azure AI Foundry
- **[PROJECT.md](./PROJECT.md)** - Detailed project architecture

## Planned Migration: React + Azure AI Foundry

The next major version will migrate to:
- **Frontend:** React + TypeScript + Fluent UI
- **Backend:** Azure Functions + Azure AI Foundry
- **LLM:** Azure OpenAI (GPT-4)

See **[docs/migration-plans/AZURE_AI_MIGRATION_PLAN.md](./docs/migration-plans/AZURE_AI_MIGRATION_PLAN.md)** for details.

## Repository Structure

```
sap-agent/
├── backend/              # FastAPI backend (V2)
│   ├── main_v2.py       # Entry point
│   ├── chat_agent_v2.py # Core agent logic
│   ├── parsers/         # Input parsers (KEEP for migration!)
│   ├── utils/           # Validators (KEEP!)
│   └── tfvars/          # TFVARS generator (KEEP!)
├── frontend/            # Streamlit frontend (V2)
│   ├── pages/chat.py    # Main chat UI
│   └── components/      # UI components
├── templates/           # Jinja2 templates
├── docs/                # All documentation
├── _archive/            # Old code (reference only)
└── data/                # SQLite database
```

## Development

See [CLAUDE.md](./CLAUDE.md) for development guidelines and architecture details.
EOF

echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "  - Documentation organized in docs/"
echo "  - Old code moved to _archive/"
echo "  - Root directory cleaned up"
echo "  - README.md updated"
echo ""
echo "📁 New structure:"
tree -L 2 -I 'venv|__pycache__|.git' .
