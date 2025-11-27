# Tech Stack 2025 - SAP Deployment Assistant
**Stand:** November 2025 (aktuellster Microsoft AI Stack)

---

## 🔥 DIE RICHTIGE TECH-STACK-ENTSCHEIDUNG

### Option A: Microsoft Agent Framework (Open-Source SDK)
**Was:** Lokales Development, Self-Hosted

```python
# Neuester Code-Style (Agent Framework)
from microsoft.agent import Agent, AgentWorkflow
from azure.ai.openai import AzureOpenAIClient

# Deine Parser bleiben unverändert!
from parsers.environment import parse_environment
from utils.validators import validate_environment

# Agent Definition (< 20 Zeilen!)
agent = Agent(
    name="SDAF Assistant",
    instructions="""You help users create SAP TFVARS files.
    Use the provided parsers and validators.""",
    functions=[parse_environment, validate_environment]
)

# Workflow (ersetzt AutoGen's Group Chat)
workflow = AgentWorkflow()
workflow.add_step("parse_input", agent)
workflow.add_step("validate", agent)
workflow.add_step("generate_tfvars", agent)

# Run
result = await workflow.run(user_message="Deploy SAP in West Europe")
```

**Pros:**
- ✅ Kostenlos (Open-Source)
- ✅ Neueste Features
- ✅ Läuft lokal (Docker)
- ✅ Volle Kontrolle

**Cons:**
- ⚠️ Public Preview (GA Q1 2026)
- ⚠️ Du hostest selbst
- ⚠️ Kein Enterprise Support

---

### Option B: Azure AI Foundry (Managed Cloud Service)
**Was:** Enterprise-ready, Microsoft-hosted

```python
# Azure AI Foundry Agent Service (GA seit Mai 2025)
from azure.ai.foundry import FoundryAgentClient

client = FoundryAgentClient(
    endpoint="https://your-foundry.cognitiveservices.azure.com",
    credential=DefaultAzureCredential()
)

# Create Agent in Portal (Visual Designer!)
# Deploy Agent
agent = client.get_agent("sdaf-assistant-v1")

# Run
response = await agent.run(
    messages=[{"role": "user", "content": "Deploy SAP"}],
    functions=[parse_environment, validate_environment]  # Deine Parser!
)
```

**Pros:**
- ✅ **GA (Production) seit Mai 2025** - voll supported!
- ✅ 99.9% SLA
- ✅ Skaliert automatisch (1000+ User)
- ✅ Visual Designer (kein Code für Workflows)
- ✅ Built-in Monitoring (App Insights)
- ✅ Multi-Model Support (GPT-4, Llama, Mistral, etc.)
- ✅ Enterprise Governance

**Cons:**
- ⚠️ Kosten: ~€300-750/Monat
- ⚠️ Vendor Lock-in (Azure)

---

## 🎯 MEINE EMPFEHLUNG FÜR DICH

### **Hybrid-Ansatz: Agent Framework + Azure AI Foundry**

```
┌──────────────────────────────────────────────────────┐
│           FRONTEND (React + Fluent UI)               │
│  - TypeScript + Vite                                 │
│  - Deployed: Azure Static Web Apps (€0-10/Monat)    │
└────────────────────┬─────────────────────────────────┘
                     │ HTTPS REST API
                     ↓
┌──────────────────────────────────────────────────────┐
│         API LAYER (Azure Functions - Python)         │
│  - Your Parsers (UNVERÄNDERT!)                       │
│  - Your Validators (UNVERÄNDERT!)                    │
│  - Your TFVARS Generator (UNVERÄNDERT!)              │
└────────────────────┬─────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ↓                       ↓
┌─────────────────────┐  ┌──────────────────────────────┐
│ Microsoft Agent     │  │ Azure AI Foundry (optional)  │
│ Framework (SDK)     │  │  - Visual Workflow Designer  │
│  - Local Dev        │  │  - Enterprise Governance     │
│  - Self-hosted      │  │  - Multi-Model Support       │
│  - Open-Source      │  │  - Monitoring                │
└─────────────────────┘  └──────────────────────────────┘
         │                       │
         └───────────┬───────────┘
                     ↓
         ┌─────────────────────────┐
         │   Azure OpenAI Service  │
         │   - GPT-4 Turbo         │
         │   - Enterprise SLA      │
         └─────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│                 DATA LAYER                           │
│  - Azure Cosmos DB (Chat History)                    │
│  - Azure Blob Storage (TFVARS Files)                 │
└──────────────────────────────────────────────────────┘
```

---

## 📦 Konkrete Implementierung

### Phase 1: Development (Agent Framework Lokal)
**Warum:** Kostenlos testen, schnell iterieren

```bash
# Setup
pip install microsoft-agent-framework
pip install azure-ai-openai

# Dein Code bleibt fast identisch!
# Nur Framework-Import ändert sich:
# OLD: from langchain import ...
# NEW: from microsoft.agent import ...
```

**Kosten:** €0 (lokal mit Azure OpenAI API calls ~€20/Monat für Dev)

---

### Phase 2: Production (Azure AI Foundry)
**Warum:** Enterprise-ready, skaliert, Support

**Setup:**
1. Azure AI Foundry Portal öffnen: https://ai.azure.com
2. Agent erstellen (Visual Designer oder Code)
3. Deine Python-Funktionen hochladen (Parser, Validators)
4. Deploy → Managed Endpoint

**Kosten:** ~€300-750/Monat (aber dafür 0 Ops-Aufwand!)

---

## 🔄 Migrations-Pfad: Streamlit → Agent Framework

### Was bleibt unverändert?
- ✅ **Alle Parser** (`parsers/`)
- ✅ **Alle Validators** (`utils/validators.py`)
- ✅ **TFVARS Generator** (`tfvars/generator.py`)
- ✅ **Templates** (`sap.tfvars.j2`)

### Was ändert sich?
| Alt (Streamlit) | Neu (Agent Framework) |
|-----------------|----------------------|
| `LangChain` | `microsoft.agent` |
| `Ollama (llama3.1)` | `Azure OpenAI (GPT-4)` |
| `st.chat_message()` | React Components |
| `SQLite` | Cosmos DB (optional) |

---

## 💻 Code-Migration: Vorher vs. Nachher

### VORHER (LangChain + Ollama)
```python
# backend/chat_agent_v2.py (aktuell)
from langchain.chat_models import ChatOllama
from langchain.schema import HumanMessage, AIMessage

llm = ChatOllama(model="llama3.1:8b")

def process_message(user_input: str):
    messages = [
        SystemMessage(content="You are SDAF assistant"),
        HumanMessage(content=user_input)
    ]
    response = llm(messages)

    # Parsing
    parsed = parse_environment(user_input)
    validated = validate_environment(parsed)

    return response.content
```

### NACHHER (Agent Framework + Azure OpenAI)
```python
# backend/chat_agent_v3.py (neu)
from microsoft.agent import Agent, FunctionTool
from azure.ai.openai import AzureOpenAIClient

# Deine Funktionen als Tools registrieren
tools = [
    FunctionTool(parse_environment),
    FunctionTool(validate_environment),
    FunctionTool(generate_tfvars)
]

# Agent erstellen
agent = Agent(
    name="SDAF Assistant",
    instructions="""You help create SAP deployment TFVARS.
    - Ask 6 questions about environment, SAP system, etc.
    - Use parse_environment() to extract data
    - Use validate_environment() to check inputs
    - Use generate_tfvars() to create final file""",
    tools=tools,
    model="gpt-4-turbo"  # Azure OpenAI
)

async def process_message(user_input: str):
    # Agent kümmert sich um alles!
    response = await agent.run(user_input)
    return response.messages[-1].content
```

**Unterschied:**
- ❌ Kein manuelles Prompt-Engineering mehr
- ❌ Kein manuelles Function-Calling
- ✅ Agent Framework macht Orchestrierung automatisch
- ✅ Deine Parser/Validators bleiben 1:1 gleich!

---

## 🚀 Start-zu-Finish Timeline

### Woche 1: Setup & Cleanup
- Tag 1: Projekt aufräumen (`cleanup_project.sh`)
- Tag 2-3: Azure Setup (AI Foundry Workspace, OpenAI)
- Tag 4-5: Agent Framework installieren & testen

### Woche 2-3: React Frontend
- ChatWindow (Fluent UI)
- Sticky Progress Bar (endlich!)
- Preview Modal
- Session Management

### Woche 4: Backend Migration
- LangChain → Agent Framework
- Ollama → Azure OpenAI
- FastAPI → Azure Functions (optional)
- SQLite → Cosmos DB (optional)

### Woche 5: Integration & Testing
- Frontend ↔ Backend verbinden
- End-to-End Tests
- Performance-Tests

### Woche 6: Production Deployment
- Deploy zu Azure Static Web Apps (Frontend)
- Deploy zu Azure Functions (Backend)
- Optional: Migrate zu Azure AI Foundry Managed Service

---

## 💰 Kosten-Kalkulation

### Variante 1: Self-Hosted (Agent Framework)
| Service | Kosten/Monat |
|---------|--------------|
| Azure Static Web Apps | €0 (Free Tier) |
| Azure Functions (Consumption) | ~€20-50 |
| Azure OpenAI (GPT-4) | ~€100-200 (1000 Chats/Tag) |
| Azure Cosmos DB (Serverless) | ~€30-50 |
| **Total** | **~€150-300/Monat** |

### Variante 2: Managed (Azure AI Foundry)
| Service | Kosten/Monat |
|---------|--------------|
| Azure AI Foundry Agent Service | ~€200-400 |
| Azure OpenAI (included) | - |
| Azure Cosmos DB | ~€30-50 |
| Static Web Apps | €0 |
| **Total** | **~€230-450/Monat** |

**Empfehlung:**
- **Dev/Testing:** Self-Hosted (€150/Monat)
- **Production:** Managed (€400/Monat) → Kein Ops-Aufwand!

---

## 📚 Resources (Neueste Links)

### Microsoft Agent Framework
- **Docs:** https://learn.microsoft.com/azure/ai-studio/agents/
- **GitHub:** https://github.com/microsoft/agent-framework
- **Quickstart:** https://learn.microsoft.com/azure/ai-studio/agents/quickstart
- **Blog:** https://devblogs.microsoft.com/foundry/introducing-microsoft-agent-framework

### Azure AI Foundry (ehemals AI Studio)
- **Portal:** https://ai.azure.com
- **Docs:** https://learn.microsoft.com/azure/ai-foundry/
- **Agent Service (GA):** https://learn.microsoft.com/azure/ai-studio/agents/overview

### React + Fluent UI
- **Fluent UI v9:** https://react.fluentui.dev/
- **Quickstart:** https://react.fluentui.dev/?path=/docs/concepts-developer-quick-start--page

---

## ✅ Decision Matrix

| Kriterium | Agent Framework (Self-Hosted) | Azure AI Foundry (Managed) |
|-----------|------------------------------|----------------------------|
| **Kosten** | ⭐⭐⭐⭐⭐ €150/Monat | ⭐⭐⭐ €400/Monat |
| **Production-Ready** | ⭐⭐⭐ Public Preview (GA Q1 2026) | ⭐⭐⭐⭐⭐ GA seit Mai 2025 |
| **Ops-Aufwand** | ⭐⭐ Du hostest selbst | ⭐⭐⭐⭐⭐ 0 Ops (Managed) |
| **Flexibilität** | ⭐⭐⭐⭐⭐ Volle Kontrolle | ⭐⭐⭐ Azure-gebunden |
| **Support** | ⭐⭐⭐ Community (GitHub) | ⭐⭐⭐⭐⭐ Enterprise SLA |
| **Skalierung** | ⭐⭐⭐ Manuell | ⭐⭐⭐⭐⭐ Automatisch |

---

## 🎯 MEINE FINALE EMPFEHLUNG

### Start: Agent Framework (Self-Hosted)
**Warum:**
- ✅ Kosteneffizient (€150/Monat)
- ✅ Neueste Features (Public Preview)
- ✅ Lernkurve gering (fast identisch zu LangChain)
- ✅ Später easy zu Foundry migrieren

### Production (später): Azure AI Foundry
**Wann:**
- ✅ Wenn >100 User/Tag
- ✅ Wenn Enterprise-Kunden (SLA nötig)
- ✅ Wenn Multi-Tenant nötig
- ✅ Wenn 0 Ops-Aufwand gewünscht

**Migration:** Nur Deployment ändert sich, Code bleibt gleich!

---

## 🚀 Next Steps

1. **JETZT:** Cleanup-Script ausführen
   ```bash
   ./cleanup_project.sh
   git commit -m "Clean up for Agent Framework migration"
   ```

2. **Morgen:** Azure Setup
   - Azure Subscription aktivieren
   - Azure OpenAI Resource erstellen
   - Agent Framework installieren

3. **Diese Woche:** React Prototype
   - Vite + React + TypeScript
   - Fluent UI Components
   - Sticky Progress Bar testen

4. **Nächste Woche:** Backend Migration
   - LangChain → Agent Framework
   - Ollama → Azure OpenAI
   - Erste End-to-End Tests

---

**TL;DR:** Nutze **Microsoft Agent Framework** (Open-Source, neuestes Zeug, €150/Monat) für Development. Später optional auf **Azure AI Foundry** (Managed, €400/Monat, 0 Ops) upgraden.
