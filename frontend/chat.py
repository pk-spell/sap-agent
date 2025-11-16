# frontend/chat.py - Vollständige, robuste Version
import streamlit as st
import requests
import uuid
import os

st.set_page_config(page_title="SDAF Jarvis", layout="wide")
st.title("🤖 SAP Deployment Automation Assistant")

# === KONFIGURATION: Dynamische API-URL ===
API_URL = os.getenv("API_URL", "http://backend:8000")
SESSIONS_URL = f"{API_URL}/list-sessions"
SAVE_URL = f"{API_URL}/save-chat"
LOAD_URL = f"{API_URL}/load-chat"
RESET_URL = f"{API_URL}/reset"

# === SESSION STATE ===
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tfvars_ready" not in st.session_state:
    st.session_state.tfvars_ready = False
if "tfvars_content" not in st.session_state:
    st.session_state.tfvars_content = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "auto_save_done" not in st.session_state:
    st.session_state.auto_save_done = False
if "backend_ready" not in st.session_state:
    st.session_state.backend_ready = False

# === BACKEND HEALTH CHECK ===
def check_backend():
    """Prüft ob Backend erreichbar ist"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.ok:
            st.session_state.backend_ready = True
            return True
    except Exception:
        st.session_state.backend_ready = False
        return False

# === HELPER: Auto-Save ===
def auto_save():
    """Speichert Session automatisch nach Fertigstellung"""
    if st.session_state.tfvars_ready and not st.session_state.auto_save_done:
        try:
            response = requests.post(SAVE_URL, json={
                "session_id": st.session_state.session_id,
                "state": {}
            }, timeout=5)
            if response.ok:
                st.session_state.auto_save_done = True
                st.toast(f"✅ Session {st.session_state.session_id} gespeichert!", icon="💾")
        except Exception as e:
            st.error(f"Auto-Save fehlgeschlagen: {e}")

# === SIDEBAR: Verbindungsstatus ===
with st.sidebar:
    st.subheader("🔌 Verbindungsstatus")
    if check_backend():
        st.success("✅ Backend verbunden")
    else:
        st.error("❌ Backend nicht erreichbar")
        st.warning("Container startet noch... Bitte warte 10-30 Sekunden.")
        if st.button("🔄 Erneut prüfen"):
            st.rerun()

# Wenn Backend nicht bereit, stoppe
if not st.session_state.backend_ready:
    st.error("🚨 Backend nicht bereit! Starte es mit: `docker compose up --build`")
    st.info("Warte bitte, bis das Backend vollständig gestartet ist.")
    st.stop()

# === CHAT-VERLAUF ANZEIGEN ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === USER INPUT ===
if prompt := st.chat_input("Deine Antwort..."):
    # Help-Intent erkennen
    if prompt.lower() in ["hilfe", "help", "?", "ich komme nicht weiter"]:
        help_text = """💡 **Du bist im Block: Environment**
        
Gib bitte **3 Werte mit Kommas** ein:
1. **Deployer**: MGMT, DEV, TST oder PRD
2. **Workload**: DEV, TST oder PRD  
3. **Region**: westeurope, northeurope, germanywestcentral

**Beispiel:** `MGMT, DEV, westeurope`

**Oder frage:** `Was ist ein SAP SID?` oder `Welche Regionen gibt es?`"""
        st.session_state.messages.append({"role": "assistant", "content": help_text})
        st.rerun()
    
    else:
        # Normale Verarbeitung
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("🤖 Bot denkt..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat", 
                    json={"message": prompt, "state": {}}, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bot_reply = data.get("reply", "Keine Antwort")
                    
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    
                    if data.get("tfvars_ready", False):
                        st.session_state.tfvars_ready = True
                        st.session_state.tfvars_content = data.get("tfvars", "")
                        auto_save()
                    
                    st.rerun()
                else:
                    st.error(f"API-Fehler: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("🚨 Backend-Verbindung abgebrochen!")
                st.session_state.backend_ready = False
                if st.button("🔄 Reconnect"):
                    st.rerun()
            except Exception as e:
                st.error(f"Verbindungsfehler: {e}")

# === DOWNLOAD BUTTON ===
if st.session_state.tfvars_ready and st.session_state.tfvars_content:
    # Hole SID aus user_answers
    sid = "config"
    try:
        # Find last user message with SAP SID pattern
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "user" and "," in msg["content"]:
                parts = [p.strip() for p in msg["content"].split(",")]
                if len(parts) == 3 and len(parts[0]) == 3:
                    sid = parts[0].upper()
                    break
    except:
        pass
    
    st.success("🎉 TFVARS erfolgreich generiert!")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.download_button(
            label="📥 TFVARS herunterladen",
            data=st.session_state.tfvars_content,
            file_name=f"{sid}.tfvars",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        with st.expander("📄 Vorschau anzeigen"):
            st.code(st.session_state.tfvars_content, language="hcl")

# === SIDEBAR: SESSION MANAGEMENT ===
with st.sidebar:
    st.subheader("💾 Session Management")
    
    # Aktuelle Session ID
    st.info(f"🆔 Aktuelle Session: **{st.session_state.session_id}**")
    
    # Manuelles Speichern
    if st.button("💾 Jetzt speichern"):
        try:
            response = requests.post(SAVE_URL, json={"session_id": st.session_state.session_id}, timeout=5)
            if response.ok:
                st.success("✅ Gespeichert!")
            else:
                st.error(f"Fehler: {response.text}")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Alle Sessions laden
    try:
        sessions = requests.get(SESSIONS_URL, timeout=5).json().get("sessions", [])
        if sessions:
            session_ids = [s["session_id"] for s in sessions]
            selected = st.selectbox("📂 Alte Session laden", session_ids)
            
            if st.button("⏳ Laden"):
                try:
                    load_resp = requests.post(LOAD_URL, json={"session_id": selected}, timeout=5)
                    if load_resp.ok and load_resp.json().get("found"):
                        st.session_state.session_id = selected
                        st.session_state.messages = []  # Wird neu geladen
                        st.session_state.auto_save_done = False
                        st.success(f"✅ Session {selected} geladen!")
                        st.rerun()
                    else:
                        st.error("Session nicht gefunden")
                except Exception as e:
                    st.error(f"Load Error: {e}")
        else:
            st.info("Noch keine Sessions gespeichert.")
    except Exception as e:
        st.error(f"Fehler beim Laden der Sessions: {e}")
    
    # Reset
    if st.button("🔄 Neu starten"):
        try:
            response = requests.post(RESET_URL, timeout=5)
            st.session_state.messages = []
            st.session_state.tfvars_ready = False
            st.session_state.tfvars_content = ""
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.auto_save_done = False
            st.success("✅ Zurückgesetzt!")
            st.rerun()
        except Exception as e:
            st.error(f"Reset Error: {e}")