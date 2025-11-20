# 🤖 SAP Deployment Automation Assistant

> AI-powered conversational tool for generating Terraform variable files (tfvars) for SAP deployments on Azure using SDAF.

[![Status](https://img.shields.io/badge/Status-Production--Ready-success)]()
[![Version](https://img.shields.io/badge/Version-2.0-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11-blue)]()

## 🚀 Quick Start

```bash
# 1. Ensure Ollama is running with llama3.1:8b
ollama run llama3.1:8b

# 2. Start the application
docker compose up --build

# 3. Open your browser
# http://localhost:8501
```

## ✨ Features

- 🎯 **Interactive Widgets** - Form-based input for key configuration steps
- 💬 **Natural Language** - Chat interface with LLM-powered parsing
- 🎨 **Smart Defaults** - 180+ SDAF parameters auto-filled
- 📊 **46 Sizing Options** - From demo systems to 4TB+ production workloads
- 💾 **Session Management** - Save, switch, and resume configurations
- ⚡ **Auto-Configuration** - Demo/Test systems configured automatically

## 🛠️ Tech Stack

**Frontend:** Streamlit | **Backend:** FastAPI + LangChain + Ollama
**Database:** SQLite | **LLM:** llama3.1:8b | **Deployment:** Docker Compose

## 📖 Documentation

**For detailed documentation, see [PROJECT.md](./PROJECT.md)**

Includes:
- Full architecture overview
- API documentation
- Database schema
- Development workflow
- Known issues & TODOs
- Code structure guide

## 🏗️ Project Structure

```
sap-agent/
├── frontend/          # Streamlit UI (fully refactored)
│   ├── components/    # Widgets, sidebar
│   ├── api/           # Backend client
│   └── pages/         # Chat interface
├── backend/           # FastAPI (partially refactored)
│   ├── models/        # Data models
│   ├── database/      # SQLite operations
│   └── utils/         # Helpers
├── templates/         # Jinja2 templates + defaults
└── data/              # SQLite database
```

## 🎯 Current Status

### ✅ Completed
- Interactive widgets for Environment & SAP System config
- Context-aware parsing (no more loops!)
- Auto-configuration for Demo/Test scenarios
- Session management with persistence
- Frontend fully refactored (modular components)

### 🔄 In Progress
- Backend refactoring (extracting parsers, prompts, tfvars)

## 🐛 Known Issues

**All critical bugs fixed!** See [PROJECT.md](./PROJECT.md#known-issues--todos) for details.

## 🤝 For Other AI Assistants

This project is designed to be AI-assistant friendly:
- **Complete documentation** in PROJECT.md
- **Modular architecture** with clear separation
- **Type hints** and docstrings throughout
- **Consistent code style** with logging

If you're Gemini, Codex, or another AI helping with this project:
1. Read [PROJECT.md](./PROJECT.md) first
2. Check current status and TODOs
3. Follow existing patterns
4. Update documentation when making changes

## 📝 License

Built with Claude Code (Anthropic) | November 2025

---

**Need help?** Check [PROJECT.md](./PROJECT.md) for detailed documentation.
