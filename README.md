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
