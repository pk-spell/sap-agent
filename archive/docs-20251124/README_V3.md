# SAP Deployment Assistant V3 🚀

**Conversational AI für SAP TFVARS Generation - Lokal mit austauschbaren LLMs**

---

## 🎯 Was ist das?

Ein KI-Assistent der dich durch 6 Fragen führt und automatisch eine komplette SAP Deployment Konfiguration (TFVARS) für Azure erstellt.

**Features:**
- ✅ **Konversational** - Chattet mit dir auf Deutsch
- ✅ **Intelligent** - Nutzt LLMs (Ollama, Claude, GPT-4, Groq)
- ✅ **Austauschbar** - LLM per Config ändern
- ✅ **Lokal** - Läuft auf deinem Rechner (€0 Kosten)
- ✅ **Production-Ready** - TypeScript, Error Handling, Tests

---

## 📦 Tech Stack V3

### Backend:
- **FastAPI** - Modern Python API
- **LLM-Factory** - Austauschbare LLMs (Ollama, Claude, GPT-4, Groq)
- **Agent V3** - Intelligenter Konversations-Agent
- **SQLite** - Session Persistence
- **Ollama** - Lokales LLM (qwen2.5:7b, llama3.1:8b)

### Frontend:
- **React 18** + **TypeScript**
- **Fluent UI v9** - Microsoft Design System
- **Vite** - Build Tool
- **TanStack Query** - Data Fetching

---

## 🚀 Quick Start

### 1. Alles starten (einfachste Methode):

```bash
./start_all.sh
```

Das startet:
- ✅ Ollama (falls nicht läuft)
- ✅ Backend (http://localhost:8000)
- ✅ Frontend (http://localhost:5173)

**Dann Browser öffnen:** http://localhost:5173

---

### 2. Manuell starten:

**Terminal 1 - Ollama:**
```bash
ollama serve
```

**Terminal 2 - Backend:**
```bash
./start_backend_v3.sh
# oder
cd backend && python3 main_v3.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend-react
npm run dev
```

---

## 🎨 UI Features

### ✅ Sticky Progress Bar
**Dein Hauptproblem gelöst!**

```css
position: sticky;
top: 0;
z-index: 1000;
```

Funktioniert perfekt in React! Kein CSS-Hack nötig.

### ✅ Fluent UI Modals
- Preview Modal (TFVARS anzeigen)
- Dialog components (kein Bug!)
- Smooth animations

### ✅ Session Management
- Sidebar mit allen Sessions
- Click to switch
- Auto-save

### ✅ Responsive Design
- Desktop optimiert
- Mobile-friendly
- Dark/Light theme ready

---

## 🔄 LLM Wechseln (3 Zeilen!)

**backend/config.yaml ändern:**

```yaml
# Ollama (Lokal, €0)
llm:
  default:
    provider: "ollama"
    model: "qwen2.5:7b"

# Claude (API)
# llm:
#   default:
#     provider: "claude"
#     model: "claude-3-5-sonnet-20241022"
#     api_key: "${CLAUDE_API_KEY}"

# OpenAI GPT-4 (API)
# llm:
#   default:
#     provider: "openai"
#     model: "gpt-4-turbo"
#     api_key: "${OPENAI_API_KEY}"

# Groq (Schnell & billig)
# llm:
#   default:
#     provider: "groq"
#     model: "llama-3.1-70b-versatile"
#     api_key: "${GROQ_API_KEY}"
```

**Fertig!** Agent nutzt automatisch das neue LLM.

---

## 📁 Projekt-Struktur

```
sap-agent/
├── backend/
│   ├── main_v3.py              # FastAPI Entry Point
│   ├── agent_v3.py             # Konversations-Agent
│   ├── llm_factory.py          # LLM-Abstraktion (austauschbar!)
│   ├── config.yaml             # LLM Configuration
│   ├── config_loader.py        # Config Loader
│   ├── parsers/                # Input Parser (UNVERÄNDERT!)
│   ├── utils/                  # Validators (UNVERÄNDERT!)
│   ├── tfvars/                 # TFVARS Generator (UNVERÄNDERT!)
│   ├── database/               # SQLite Operations
│   └── models/                 # Data Models
│
├── frontend-react/
│   ├── src/
│   │   ├── App.tsx             # Main App (sticky Progress!)
│   │   ├── main.tsx            # Entry Point
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx  # Chat Interface
│   │   │   ├── ChatMessage.tsx # Message Component
│   │   │   ├── SessionList.tsx # Sidebar Sessions
│   │   │   └── PreviewModal.tsx# TFVARS Preview
│   │   ├── api/
│   │   │   └── client.ts       # Backend API Client
│   │   └── types/
│   │       └── index.ts        # TypeScript Types
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── templates/
│   ├── easy_defaults.yaml      # Default Values
│   └── sap.tfvars.j2          # Jinja2 Template
│
├── docs/                       # Dokumentation
│   ├── MIGRATION_COMPLETE.md  # Migration Summary
│   ├── REACT_SETUP_INSTRUCTIONS.md
│   └── LOCAL_FIRST_ARCHITECTURE.md
│
├── start_all.sh               # Start Backend + Frontend
├── start_backend_v3.sh        # Start Backend only
└── README_V3.md               # Diese Datei
```

---

## 🎓 Konversationsflow

Der Agent führt dich durch **6 Schritte**:

1. **Environment** (Deployer, Workload Zone, Region)
2. **SAP System** (SID, Product, Environment)
3. **Sizing** (VM Size, Memory, Disks)
4. **Architecture** (High Availability, Distributed)
5. **Network** (VNet, Subnets, NSG)
6. **OS Selection** (SLES, RHEL, Windows)

**Dann:** TFVARS wird automatisch generiert! 🎉

---

## 💰 Kosten

### Lokal (Ollama):
- **€0 / Monat**
- Unbegrenzte Requests
- 100% Datenschutz
- Offline-fähig (nach Setup)

### Cloud (Optional):
- **Claude:** ~€15/1M tokens
- **GPT-4:** ~€10/1M tokens
- **Groq:** €0.59/1M tokens

**Empfehlung:** Start lokal (€0), später Cloud wenn nötig!

---

## 🐛 Troubleshooting

### Backend startet nicht:
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check Backend Health
curl http://localhost:8000/health
```

### Frontend startet nicht:
```bash
# Dependencies installieren
cd frontend-react
npm install

# Port 5173 belegt?
# In vite.config.ts ändern: port: 3000
```

### LLM Fehler:
```bash
# Prüfe welches Model verfügbar
ollama list

# Download qwen2.5:7b
ollama pull qwen2.5:7b

# Test LLM-Factory
cd backend
python3 -c "from llm_factory import get_ollama_llm; print('OK')"
```

### WSL npm Issues:
```bash
# In Windows CMD stattdessen:
cd \\wsl$\Ubuntu-22.04\home\kuschi\sap-agent\frontend-react
npm install
```

---

## 📚 Dokumentation

### Haupt-Docs:
- **MIGRATION_COMPLETE.md** - Was wurde gebaut?
- **LOCAL_FIRST_ARCHITECTURE.md** - Lokale Architektur (€0)
- **TECH_STACK_2025.md** - Microsoft AI Stack Details
- **REACT_SETUP_INSTRUCTIONS.md** - Frontend Setup

### API Docs:
- **Backend:** http://localhost:8000/docs (Swagger)
- **Code:** Alle Dateien haben Kommentare

---

## 🎯 Use Cases

### Development:
- ✅ Lokal mit Ollama (€0)
- ✅ Schnell iterieren
- ✅ Volle Kontrolle

### Testing:
- ✅ Verschiedene LLMs testen
- ✅ Claude vs GPT-4 vergleichen
- ✅ Prompt-Engineering

### Production:
- ✅ Deploy zu Azure
- ✅ Multi-User Support
- ✅ Enterprise SLA

---

## 🔥 Highlights

### Backend:
```python
# LLM in 3 Zeilen wechseln:
from config_loader import get_config
config = get_config()
llm = config.get_llm("default")  # Liest config.yaml!
```

### Frontend:
```tsx
// Sticky Progress Bar (funktioniert!):
<div className={styles.progressContainer}>
  <ProgressBar value={progress / 100} />
</div>
```

---

## 🚀 Nächste Schritte

### Jetzt:
1. `./start_all.sh`
2. Browser: http://localhost:5173
3. Chat mit Agent
4. TFVARS generieren
5. Download

### Später:
1. LLM wechseln (config.yaml)
2. Cloud-Migration (Optional)
3. Weitere Features bauen

---

## 🙏 Credits

- **Backend:** FastAPI, LangChain, Ollama
- **Frontend:** React, Fluent UI (Microsoft)
- **LLM:** qwen2.5:7b (Alibaba), llama3.1:8b (Meta)

---

## 📄 License

Internes Projekt - Nicht für öffentliche Nutzung ohne Genehmigung.

---

## 🎉 Fertig!

Du hast jetzt:
- ✅ Production-ready Backend + Frontend
- ✅ Sticky Progress Bar (GELÖST!)
- ✅ LLM austauschbar (config.yaml)
- ✅ 100% lokal (€0 Kosten)
- ✅ Cloud-ready (später)

**Viel Erfolg mit deinem SAP Deployment Assistant V3!** 🚀
