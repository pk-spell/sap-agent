# Azure AI Foundry Migration Plan
## SAP Deployment Assistant - Production Architecture

**Datum:** 2025-11-20
**Status:** Planungsphase
**Ziel:** Production-ready Enterprise App für SAP-Kunden

---

## 🎯 Warum Azure AI Foundry?

### Aktuelle Probleme mit Streamlit + Ollama

| Problem | Impact | Azure AI Lösung |
|---------|--------|-----------------|
| **UI-Limitierungen** | Sticky headers, modals schwierig | React + Fluent UI = vollständige Kontrolle |
| **Performance** | Langsam bei vielen Usern | Azure Skalierung automatisch |
| **LLM-Hosting** | Lokales Ollama = nicht produktiv | Azure OpenAI = Enterprise SLA |
| **Kein Microsoft-Look** | SAP-User erwarten Office 365-Style | Fluent UI = identisch zu Azure Portal |
| **State-Management** | st.session_state kompliziert | React Context + Azure Cosmos DB |
| **Multi-Tenant** | Nicht möglich | Azure AD B2C integriert |

---

## 🏗️ Neue Architektur

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  - React 18 + TypeScript                                    │
│  - Fluent UI v9 (Microsoft Design System)                   │
│  - Deployed: Azure Static Web Apps                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/REST
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              API LAYER (Azure Functions)                     │
│  - Python 3.11 Azure Functions                              │
│  - FastAPI → Azure Functions Adapter                        │
│  - Auth: Azure AD B2C                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ↓                       ↓
┌────────────────────┐  ┌────────────────────────────┐
│ Azure AI Foundry   │  │ Backend Services (Python)  │
│  - Prompt Flow     │  │  - Parser (BEHALTEN!)      │
│  - GPT-4 Turbo     │  │  - Validators (BEHALTEN!)  │
│  - Semantic Kernel │  │  - TFVARS Gen (BEHALTEN!)  │
└────────────────────┘  └────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│              STORAGE & DATA                                  │
│  - Azure Cosmos DB (Chat History, Sessions)                 │
│  - Azure Blob Storage (Generated TFVARS)                    │
│  - Azure Key Vault (Secrets, API Keys)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Tech Stack im Detail

### Frontend
```json
{
  "framework": "React 18",
  "language": "TypeScript",
  "ui": "@fluentui/react-components v9",
  "state": "React Context + TanStack Query",
  "routing": "React Router v6",
  "build": "Vite",
  "deployment": "Azure Static Web Apps"
}
```

### Backend
```json
{
  "runtime": "Python 3.11",
  "functions": "Azure Functions v4",
  "api": "FastAPI (adapted for Functions)",
  "ai": "Azure AI Foundry + Prompt Flow",
  "llm": "Azure OpenAI GPT-4 Turbo",
  "database": "Azure Cosmos DB (NoSQL)",
  "storage": "Azure Blob Storage"
}
```

---

## 🔄 Migration Strategy

### Phase 1: Preparation (Week 1)

#### Tasks:
1. **Azure Setup**
   - [ ] Create Azure Subscription (oder bestehende nutzen)
   - [ ] Setup Resource Group: `rg-sdaf-assistant-prod`
   - [ ] Create Azure AI Foundry Projekt
   - [ ] Deploy Azure OpenAI Resource (GPT-4)
   - [ ] Setup Cosmos DB Account
   - [ ] Create Blob Storage Account

2. **Repository Setup**
   - [ ] Create `/frontend-react` Ordner
   - [ ] Initialize Vite + React + TypeScript
   - [ ] Install Fluent UI v9
   - [ ] Setup ESLint + Prettier

3. **Backend Anpassungen**
   - [ ] Convert FastAPI zu Azure Functions
   - [ ] Migrate SQLite → Cosmos DB
   - [ ] **Parser/Validators unverändert übernehmen**

#### Deliverables:
- ✅ Azure Infrastruktur steht
- ✅ Leeres React-Projekt läuft
- ✅ Backend-Adapter für Azure Functions

---

### Phase 2: Frontend Development (Week 2-3)

#### Component-Struktur (React)

```
frontend-react/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWindow.tsx          # Main chat interface
│   │   │   ├── ChatMessage.tsx         # Single message component
│   │   │   ├── ChatInput.tsx           # User input field
│   │   │   └── ProgressIndicator.tsx   # Sticky progress bar
│   │   ├── Preview/
│   │   │   ├── TFVarsPreview.tsx       # Preview modal
│   │   │   └── PreviewButton.tsx       # Trigger button
│   │   ├── Sidebar/
│   │   │   ├── SessionList.tsx         # All sessions
│   │   │   └── SessionCard.tsx         # Single session
│   │   └── Common/
│   │       ├── Header.tsx              # App header
│   │       └── Layout.tsx              # Page layout
│   ├── hooks/
│   │   ├── useChat.ts                  # Chat logic
│   │   ├── useSessions.ts              # Session management
│   │   └── usePreview.ts               # Preview data
│   ├── services/
│   │   ├── api.ts                      # API client
│   │   └── auth.ts                     # Azure AD B2C
│   ├── types/
│   │   ├── chat.ts                     # Chat types
│   │   └── session.ts                  # Session types
│   ├── App.tsx                         # Root component
│   └── main.tsx                        # Entry point
├── package.json
└── vite.config.ts
```

#### Key Components (Codebeispiele)

**ChatWindow.tsx** (Fluent UI)
```tsx
import {
  makeStyles,
  tokens,
  Card
} from '@fluentui/react-components';
import { useChat } from '../hooks/useChat';

const useStyles = makeStyles({
  container: {
    backgroundColor: tokens.colorNeutralBackground1,
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: tokens.spacingVerticalL,
  },
});

export const ChatWindow = () => {
  const styles = useStyles();
  const { messages, sendMessage } = useChat();

  return (
    <div className={styles.container}>
      <ProgressIndicator /> {/* Sticky! */}

      <div className={styles.messages}>
        {messages.map(msg => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>

      <ChatInput onSend={sendMessage} />
    </div>
  );
};
```

**useChat.ts** (Custom Hook)
```tsx
import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useChat = (sessionId: string) => {
  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => api.getSession(sessionId),
  });

  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      api.sendMessage(sessionId, message),
  });

  const sendMessage = useCallback(async (text: string) => {
    await sendMutation.mutateAsync(text);
  }, [sendMutation]);

  return {
    messages: session?.messages ?? [],
    sendMessage,
    isLoading: sendMutation.isPending,
  };
};
```

#### Tasks:
- [ ] Implement ChatWindow + ChatMessage
- [ ] Build ProgressIndicator (sticky!)
- [ ] Create TFVarsPreview Modal (Fluent UI Dialog)
- [ ] Implement SessionList Sidebar
- [ ] Add Dark/Light Theme Toggle
- [ ] Responsive Design (Mobile + Desktop)

#### Deliverables:
- ✅ Vollständiges React Frontend
- ✅ Fluent UI Components integriert
- ✅ Responsive Design

---

### Phase 3: Azure AI Foundry Integration (Week 3)

#### Prompt Flow Setup

**Warum Prompt Flow statt direktem GPT-4 Call?**
- ✅ Visual Designer für Agent-Logik
- ✅ Built-in Evaluation & Testing
- ✅ Version Control für Prompts
- ✅ A/B Testing möglich

**Flow-Struktur:**
```
User Input
    ↓
[Intent Detection Node]
    ↓
[Validation Node] ← Calls Python Function (unsere Validators!)
    ↓
[LLM Parsing Node] ← GPT-4 Turbo
    ↓
[TFVARS Generation] ← Python Function (behalten!)
    ↓
Response
```

#### Prompt Flow YAML (Beispiel)

```yaml
# prompt-flow.yaml
$schema: https://azuremlschemas.azureedge.net/promptflow/latest/Flow.schema.json

inputs:
  user_message:
    type: string
  session_data:
    type: object

outputs:
  assistant_message:
    type: string
  updated_data:
    type: object

nodes:
  # Node 1: Intent Detection
  - name: detect_intent
    type: llm
    source:
      type: code
      path: detect_intent.jinja2
    inputs:
      deployment_name: gpt-4
      temperature: 0.3
      max_tokens: 100
      message: ${inputs.user_message}

  # Node 2: Validation (Python)
  - name: validate_input
    type: python
    source:
      type: code
      path: validate.py  # Unsere validators.py!
    inputs:
      user_input: ${inputs.user_message}
      intent: ${detect_intent.output}

  # Node 3: Parse with LLM
  - name: parse_llm
    type: llm
    source:
      type: code
      path: parse_prompt.jinja2
    inputs:
      deployment_name: gpt-4
      temperature: 0.1
      user_message: ${inputs.user_message}
      validation_result: ${validate_input.output}

  # Node 4: Generate TFVARS (Python)
  - name: generate_tfvars
    type: python
    source:
      type: code
      path: tfvars_generator.py  # Unsere generator.py!
    inputs:
      user_data: ${parse_llm.output}
```

#### Tasks:
- [ ] Create Azure AI Foundry Flow
- [ ] Migrate Prompts zu Prompt Flow
- [ ] Integrate Python Validators (unverändert!)
- [ ] Test Flow mit verschiedenen Inputs
- [ ] Deploy Flow zu Azure

#### Deliverables:
- ✅ Prompt Flow deployed
- ✅ Python-Code integriert
- ✅ End-to-End Test erfolgreich

---

### Phase 4: Backend Migration (Week 4)

#### Azure Functions Structure

```
backend-azure/
├── function_app.py              # Main Functions App
├── functions/
│   ├── chat.py                  # POST /sessions/{id}/chat
│   ├── sessions.py              # GET/POST /sessions
│   ├── preview.py               # GET /sessions/{id}/preview
│   └── health.py                # GET /health
├── parsers/                     # UNVERÄNDERT aus Streamlit-Version!
│   ├── environment.py
│   ├── sap_system.py
│   └── ...
├── utils/                       # UNVERÄNDERT!
│   ├── validators.py
│   └── ...
├── tfvars/                      # UNVERÄNDERT!
│   └── generator.py
├── requirements.txt
└── host.json                    # Azure Functions Config
```

#### Azure Functions Adapter (FastAPI → Functions)

```python
# function_app.py
import azure.functions as func
from parsers.environment import parse_environment_input
from utils.validators import validate_environment
from services.ai_foundry import call_prompt_flow

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="sessions/{session_id}/chat", methods=["POST"])
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    session_id = req.route_params.get('session_id')
    body = req.get_json()
    user_message = body.get('message')

    # Call Azure AI Foundry Prompt Flow
    result = await call_prompt_flow(
        user_message=user_message,
        session_id=session_id
    )

    return func.HttpResponse(
        body=json.dumps(result),
        mimetype="application/json"
    )
```

#### Cosmos DB Integration

```python
# services/database.py
from azure.cosmos import CosmosClient

client = CosmosClient(url, key)
database = client.get_database_client('sdaf-assistant')
sessions_container = database.get_container_client('sessions')

async def save_session(session_data):
    await sessions_container.upsert_item(session_data)

async def get_session(session_id):
    return await sessions_container.read_item(
        item=session_id,
        partition_key=session_id
    )
```

#### Tasks:
- [ ] Convert FastAPI zu Azure Functions
- [ ] Integrate Cosmos DB
- [ ] Setup Blob Storage für TFVARS
- [ ] Add Azure AD B2C Auth
- [ ] Test all endpoints

#### Deliverables:
- ✅ Azure Functions deployed
- ✅ Cosmos DB funktioniert
- ✅ Auth implementiert

---

## 💰 Kosten-Schätzung (Azure)

### Monatliche Kosten (Production)

| Service | Tier | Kosten/Monat | Notizen |
|---------|------|--------------|---------|
| **Azure OpenAI** | GPT-4 Turbo | ~€200-500 | 1000 Chats/Tag |
| **Azure Functions** | Consumption | ~€20-50 | Pay-per-execution |
| **Cosmos DB** | Serverless | ~€30-80 | NoSQL, auto-scale |
| **Static Web Apps** | Free/Standard | €0-10 | Frontend hosting |
| **Blob Storage** | Standard | ~€5 | TFVARS files |
| **AI Foundry** | Pay-as-go | ~€50-100 | Prompt Flow |
| **Application Insights** | Basic | ~€10 | Monitoring |

**Total:** ~€315-750/Monat für Production

**Entwicklung:** ~€50-100/Monat (kleinere Tiers)

---

## 📊 Feature-Vergleich

| Feature | Streamlit (Current) | Azure AI (Planned) |
|---------|--------------------|--------------------|
| **UI-Flexibilität** | ⭐⭐ Limitiert | ⭐⭐⭐⭐⭐ Vollständig |
| **Performance** | ⭐⭐ 10 User max | ⭐⭐⭐⭐⭐ 1000+ User |
| **Sticky Headers** | ⭐⭐ CSS-Hacks | ⭐⭐⭐⭐⭐ Native |
| **Modals** | ⭐⭐⭐ st.dialog (buggy) | ⭐⭐⭐⭐⭐ Fluent Dialog |
| **Mobile Support** | ⭐⭐ Begrenzt | ⭐⭐⭐⭐⭐ Vollständig |
| **Auth** | ❌ Nicht vorhanden | ⭐⭐⭐⭐⭐ Azure AD B2C |
| **Multi-Tenant** | ❌ Unmöglich | ⭐⭐⭐⭐⭐ Built-in |
| **LLM-Qualität** | ⭐⭐⭐ Ollama (lokal) | ⭐⭐⭐⭐⭐ GPT-4 Turbo |
| **Monitoring** | ❌ Keine | ⭐⭐⭐⭐⭐ App Insights |
| **SAP-Look** | ⭐⭐ Custom CSS | ⭐⭐⭐⭐⭐ Fluent UI |

---

## ⚠️ Risiken & Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **Learning Curve (React)** | Hoch | Mittel | Tutorials, Template verwenden |
| **Azure Kosten** | Mittel | Hoch | Start mit Free Tier, Monitoring |
| **Migration Zeit** | Mittel | Mittel | Parallel-Entwicklung |
| **Python → JS Übersetzung** | Niedrig | Niedrig | Parser bleibt Python! |

---

## 🎯 Success Metrics

### Migration erfolgreich wenn:
- ✅ React Frontend läuft in Production
- ✅ Azure AI Foundry Flow funktioniert
- ✅ Parser/Validators unverändert übernommen
- ✅ < 2s Response Time
- ✅ 100+ gleichzeitige User möglich
- ✅ Microsoft-Look (Fluent UI)
- ✅ Sticky Progress Bar funktioniert
- ✅ Preview Modal ohne Bugs

---

## 📅 Timeline

```
Week 1:  Azure Setup + Repo Prep
Week 2:  React Frontend Development
Week 3:  Azure AI Foundry Integration
Week 4:  Backend Migration + Testing
Week 5:  QA + Bugfixes
Week 6:  Production Deployment

Total: 6 Wochen (1.5 Monate)
```

---

## 🚀 Next Steps

### Sofort (Diese Woche):
1. Streamlit MVP fertigstellen (für Tests)
2. Azure Subscription aktivieren
3. React-Template erstellen

### Nächste Woche:
1. Azure Infrastruktur aufsetzen
2. Erste React-Components bauen
3. Prompt Flow Prototyp

---

## 📚 Resources

- **Azure AI Foundry Docs:** https://learn.microsoft.com/azure/ai-studio
- **Fluent UI v9:** https://react.fluentui.dev/
- **React + TypeScript:** https://react.dev/learn/typescript
- **Azure Functions Python:** https://learn.microsoft.com/azure/azure-functions/functions-reference-python
- **Prompt Flow Tutorial:** https://microsoft.github.io/promptflow/

---

**TL;DR:** Migration lohnt sich für Production, dauert 6 Wochen, kostet ~€300-750/Monat, behält aber all unsere Python-Parser!
