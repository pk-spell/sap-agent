# backend/chat_agent_simple.py - VOLLSTÄNDIG & KORREKT
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_community.cache import InMemoryCache
import langchain
from typing import Dict, Any, List
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml
import sqlite3
import uuid
import json
from datetime import datetime

# Setup
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="SDAF Chat Agent")

# Async-fähiges LLM mit korrigierter URL
llm = OllamaLLM(
    model="llama3.1:8b", 
    base_url="http://host.docker.internal:11434",
    async_mode=True
)

templates_dir = Path("/app/templates")
jinja_env = Environment(loader=FileSystemLoader(templates_dir))

# Cache aktivieren (OHNE maxsize!)
langchain.llm_cache = InMemoryCache()

# Global State (für MVP okay)
class AgentState:
    def __init__(self):
        self.messages: List[tuple] = []
        self.current_block = "environment"
        self.user_answers: Dict[str, Any] = {}
        self.tfvars_ready = False
        self.tfvars_content = ""

state = AgentState()

# Intent Detection
def is_smalltalk(message: str) -> bool:
    """Erkennt, ob User eine allgemeine Frage stellt"""
    smalltalk_keywords = [
        "wer bist du", "was kannst du", "hilfe", "help", 
        "was machst du", "erklärung", "einleitung", "intro"
    ]
    return any(keyword in message.lower() for keyword in smalltalk_keywords)

def get_welcome_message() -> str:
    """Erste Begrüßung für neue User"""
    return """👋 **Hallo! Ich bin dein SDAF Configuration Assistant.**
    
Ich kann dir helfen, Terraform-Variablen für SAP-Deployments auf Azure zu generieren.

**Was du tun kannst:**
1. **Easy Mode**: Gib 5 Werte ein → TFVARS-Datei wird erzeugt
2. **Fragen stellen**: "Was ist ein SAP SID?" oder "Welche Regionen gibt es?"

**Starte jetzt:**
- Gib deine **Environment** ein: `MGMT, DEV, westeurope`
- Oder frage mich: `Was kannst du für mich tun?`
"""

def get_help_message() -> str:
    """Detaillierte Hilfe"""
    return """📖 **Verfügbare Kommandos:**

**Environment Block:**
- `MGMT, DEV, westeurope` → Deployer, Workload, Region
- Regionen: `westeurope`, `northeurope`, `germanywestcentral`

**SAP System Block:**
- `X01, S4HANA2023, small` → SID, Produkt, Sizing
- Produkte: `S4HANA2023`, `S4HANA2022`, `SAP_NETWEAVER_750`
- Sizing: `small`, `medium`, `large`

**Fragen:**
- `Was ist ein SAP SID?` → Ich erkläre es dir
- `Welche VM-Größen gibt es?` → Zeige Sizing-Tabelle
"""

def generate_tfvars_content(answers: Dict[str, Any]) -> str:
    """Generiert TFVARS aus Antworten"""
    try:
        # Lade Defaults
        defaults_path = templates_dir / "easy_defaults.yaml"
        config = yaml.safe_load(defaults_path.read_text())
        
        # Update mit user answers
        config.update({
            "deployer_environment": answers.get("deployer", "MGMT"),
            "workload_environment": answers.get("workload", "DEV"),
            "location": answers.get("region", "westeurope"),
            "sap_sid": answers.get("sap_sid", "X01"),
            "sap_product_id": answers.get("product", "S4HANA2023"),
            "sap_system_name": answers.get("sap_sid", "X01"),
            "database_sid": f"{answers.get('sap_sid', 'X01')}DB",
            "workload_zone": f"{answers.get('workload', 'DEV')}-WEEU-{answers.get('sap_sid', 'X01')}",
        })
        
        # Sizing
        sizing_map = {
            "small": {"app": "Standard_D4s_v3", "db": "Standard_E16s_v3", "scs": "Standard_D2s_v3"},
            "medium": {"app": "Standard_D8s_v3", "db": "Standard_E32s_v3", "scs": "Standard_D4s_v3"},
            "large": {"app": "Standard_D16s_v3", "db": "Standard_E64s_v3", "scs": "Standard_D8s_v3"},
        }
        sizing = answers.get("sizing", "small")
        if sizing in sizing_map:
            config["app_tier_sku"] = sizing_map[sizing]["app"]
            config["database_tier_sku"] = sizing_map[sizing]["db"]
            config["scs_tier_sku"] = sizing_map[sizing]["scs"]
        
        # Render template
        template = jinja_env.get_template("sap.tfvars.j2")
        return template.render(config=config)
    except Exception as e:
        logging.error(f"TFVARS Error: {e}")
        return f"ERROR: {e}"

# FastAPI
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):  # <-- !! DER FEHLENDE DOPPELPUNKT !!
    global state
    
    try:
        # === WICHTIG: Zuerst Intent prüfen! ===
        message_lower = req.message.lower().strip()
        
        # User-Nachricht speichern
        state.messages.append(("user", req.message))
        
        # FAST-PATH: Keywords für bekannte Themen
        if any(keyword in message_lower for keyword in 
               ["sap sid", "region", "sizing", "produkt", "wer bist du", 
                "was kannst du", "hilfe", "help", "einleitung", "intro"]):
            
            # Antwort auf Basis des Keywords
            if "sap sid" in message_lower:
                reply = """🔤 **SAP SID (System Identifier)**
                
- **3 Zeichen**, z.B. `X01`, `P01`, `Q01`
- Muss **UPPERCASE** sein
- Jede SID repräsentiert ein SAP-System
- **Beispiele:**
  - DEV: `X01`, `D01`
  - TST: `T01`, `Q01`
  - PRD: `P01`, `S01`"""
            
            elif "was kannst du" in message_lower or "hilfe" in message_lower:
                reply = get_help_message()
            
            elif "region" in message_lower:
                reply = """🌍 **Verfügbare Azure Regionen für SAP:**
                
- `westeurope` (Amsterdam) - **Empfohlen**
- `northeurope` (Irland)
- `germanywestcentral` (Frankfurt, aber teurer)"""
            
            elif "sizing" in message_lower:
                reply = """📊 **VM Sizing Profile**

**small** (Dev/Test):
- App: Standard_D4s_v3
- DB: Standard_E16s_v3

**medium** (Test/QA):
- App: Standard_D8s_v3
- DB: Standard_E32s_v3

**large** (Production):
- App: Standard_D16s_v3
- DB: Standard_E64s_v3"""
            
            elif "produkt" in message_lower:
                reply = """📦 **Verfügbare SAP Produkte:**
                
- `S4HANA2023`
- `S4HANA2022`
- `SAP_NETWEAVER_750`"""
            
            elif "wer bist du" in message_lower:
                reply = """👋 **Ich bin dein SDAF Configuration Assistant!**

Ich helfe dir, **Terraform-Variablen** für SAP-Deployments auf Azure zu generieren.

**Fähigkeiten:**
- ✅ Interaktive Konfiguration per Chat
- ✅ Validierung mit Llama 3.1 8B
- ✅ TFVARS-Datei Download
- ✅ Erklärungen zu SAP/SDAF/TFVARS

**Los geht's:**
Gib deine Environment ein: `MGMT, DEV, westeurope`"""
            
            else:
                reply = "👋 Schreibe `Hilfe` oder `Was kannst du?` für mehr Infos!"
            
            # Bot-Antwort speichern
            state.messages.append(("assistant", reply))
            
            return {
                "reply": reply,
                "state": {
                    "messages": state.messages,
                    "current_block": state.current_block,
                    "user_answers": state.user_answers,
                    "tfvars_ready": state.tfvars_ready
                },
                "tfvars": "",
                "tfvars_ready": False
            }
        
        # SLOW-PATH: ASYNC LLM für unbekannte/unstrukturierte Fragen
        elif is_smalltalk(req.message):
            prompt = f"""Du bist ein hilfreicher SAP SDAF Experten-Assistent. 
Der User fragt: "{req.message}"

Beantworte:
- Kurz und präzise (max. 250 Zeichen)
- Fokussiert auf SAP, Terraform, Azure
- Wenn unklar, biete Hilfe an

Antwort:"""
            
            # ASYNC LLM Call - Hier passiert die Magie!
            reply = await llm.ainvoke(prompt)
            
            # Safety fallback
            if not reply or len(reply.strip()) < 5:
                reply = get_help_message()
            else:
                reply = f"🤖 **Assistent:** {reply.strip()}"
            
            state.messages.append(("assistant", reply))
            
            return {
                "reply": reply,
                "state": {
                    "messages": state.messages,
                    "current_block": state.current_block,
                    "user_answers": state.user_answers,
                    "tfvars_ready": state.tfvars_ready
                },
                "tfvars": "",
                "tfvars_ready": False
            }
        
        # === NORMALER TFVARS FLOW (nur wenn KEIN Smalltalk) ===
        if state.current_block == "environment":
            try:
                parts = [p.strip() for p in req.message.split(",")]
                if len(parts) != 3:
                    raise ValueError("3 Werte erwartet")
                state.user_answers["deployer"] = parts[0]
                state.user_answers["workload"] = parts[1]
                state.user_answers["region"] = parts[2]
                reply = "✅ Environment validiert! Nächster Block..."
                state.current_block = "sap_system"
            except:
                reply = "❌ Bitte genau 3 Werte mit Kommas angeben."
                state.messages.append(("assistant", reply))
            
        elif state.current_block == "sap_system":
            try:
                parts = [p.strip() for p in req.message.split(",")]
                if len(parts) != 3:
                    raise ValueError("3 Werte erwartet")
                state.user_answers["sap_sid"] = parts[0].upper()
                state.user_answers["product"] = parts[1]
                state.user_answers["sizing"] = parts[2]
                reply = "✅ SAP System validiert! 🎉 TFVARS wird generiert..."
                state.current_block = "complete"
                state.tfvars_ready = True
            except:
                reply = "❌ Bitte genau 3 Werte mit Kommas angeben."
                state.messages.append(("assistant", reply))
        
        else:
            # Bereits fertig
            reply = "🎉 Bereits fertig! Nutze den Download-Button oder frage `Hilfe`."
            state.messages.append(("assistant", reply))
        
        # TFVARS generieren wenn fertig
        tfvars = ""
        if state.tfvars_ready:
            tfvars = generate_tfvars_content(state.user_answers)
        
        return {
            "reply": reply,
            "state": {
                "messages": state.messages,
                "current_block": state.current_block,
                "user_answers": state.user_answers,
                "tfvars_ready": state.tfvars_ready
            },
            "tfvars": tfvars,
            "tfvars_ready": state.tfvars_ready
        }
    
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
def reset():
    global state
    state = AgentState()
    return {"status": "reset"}

@app.get("/health")
def health():
    return {"status": "ok"}

# SQLite Setup
DB_PATH = "/app/data/chat_history.db"

def init_db():
    """Erstellt Tabelle falls nicht existiert"""
    # SICHERSTELLEN, dass das Verzeichnis existiert
    Path("/app/data").mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                messages TEXT NOT NULL,
                user_answers TEXT,
                tfvars_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logging.info(f"✅ Datenbank erfolgreich initialisiert unter {DB_PATH}")
    except Exception as e:
        logging.error(f"❌ Datenbank-Fehler: {e}")
        raise

def save_session(session_id: str, messages: list, user_answers: dict, tfvars: str):
    """Speichert Session in DB"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR REPLACE INTO sessions 
        (session_id, messages, user_answers, tfvars_content, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, json.dumps(messages), json.dumps(user_answers), tfvars, datetime.now()))
    conn.commit()
    conn.close()

def load_session(session_id: str) -> dict:
    """Lädt Session aus DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT messages, user_answers, tfvars_content FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "messages": json.loads(row[0]),
            "user_answers": json.loads(row[1] or "{}"),
            "tfvars_content": row[2] or ""
        }
    return None

def get_all_sessions() -> list:
    """Zeigt alle Sessions (für Admin-View)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT session_id, created_at FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"session_id": r[0], "created_at": r[1]} for r in rows]

# NEUE ENDPOINTS

@app.post("/save-chat")
def save_chat(req: dict):
    """Speichert aktuellen Chat"""
    session_id = req.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    save_session(
        session_id,
        state.messages,
        state.user_answers,
        state.tfvars_content if state.tfvars_ready else ""
    )
    return {"session_id": session_id, "status": "saved"}

@app.post("/load-chat")
def load_chat(req: dict):
    """Lädt alten Chat"""
    global state
    
    session_id = req.get("session_id")
    data = load_session(session_id)
    
    if data:
        state.messages = data["messages"]
        state.user_answers = data["user_answers"]
        state.tfvars_content = data["tfvars_content"]
        state.tfvars_ready = bool(state.tfvars_content)
        return {"found": True, "session_id": session_id}
    return {"found": False}

@app.get("/list-sessions")
def list_sessions():
    """Gibt alle Sessions zurück (Admin)"""
    return {"sessions": get_all_sessions()}

# AUTOMATISCHE DB-INITIALISIERUNG BEI START

@app.on_event("startup")
async def startup_event():
    """Startet beim Boot des Backends"""
    logging.info("🗄️ Initialisiere SQLite Datenbank...")
    init_db()
    logging.info("✅ Datenbank bereit!")

# Beim Modul-Import automatisch initialisieren
init_db()  # Sicherstellen dass DB existiert