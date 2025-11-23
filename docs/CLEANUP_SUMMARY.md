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
