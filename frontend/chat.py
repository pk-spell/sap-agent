import streamlit as st
import requests

st.set_page_config(page_title="SDAF Jarvis", layout="wide")
st.title("🤖 SAP Deployment Automation Assistant")

API_URL = "http://backend:8000/chat"

# === SESSION STATE ===
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tfvars_ready" not in st.session_state:
    st.session_state.tfvars_ready = False
if "tfvars_content" not in st.session_state:
    st.session_state.tfvars_content = ""

# === CHAT-VERLAUF ANZEIGEN ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === USER INPUT (immer zuerst) ===
if prompt := st.chat_input("Deine Antwort..."):
    # User-Nachricht speichern
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Bot-Antwort laden
    with st.spinner("🤖 Bot denkt..."):
        try:
            response = requests.post(API_URL, json={"message": prompt, "state": {}}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                bot_reply = data.get("reply", "Keine Antwort")
                
                # Bot-Antwort speichern
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
                # TFVARS-Status aktualisieren (wichtig: IM STATE!)
                if data.get("tfvars_ready", False):
                    st.session_state.tfvars_ready = True
                    st.session_state.tfvars_content = data.get("tfvars", "")
                    # Sidebar sofort aktualisieren
                    with st.sidebar:
                        st.success("✅ TFVARS bereit!")
                
                st.rerun()  # Neu rendern, damit Button erscheint
            else:
                st.error(f"API-Fehler: {response.status_code}")
        except Exception as e:
            st.error(f"Verbindungsfehler: {e}")

# === DOWNLOAD BUTTON (AUSSERHALB der Eingabe-Bedingung!) ===
# Dieser Block läuft IMMER nach dem Reload
if st.session_state.tfvars_ready and st.session_state.tfvars_content:
    # Hole SID aus letzter Nachricht (oder Default)
    last_msg = st.session_state.messages[-1]["content"] if st.session_state.messages else ""
    sid = "config"
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and "validiert" in msg["content"]:
            # Parsen aus user_answers wäre besser, aber Kompromiss für MVP
            sid = "X01"  # Fallback, du kannst das verbessern
            break
    
    st.success("🎉 TFVARS erfolgreich generiert!")
    
    # Button im Hauptfenster
    col1, col2 = st.columns([1, 2])
    with col1:
        st.download_button(
            label="📥 TFVARS herunterladen",
            data=st.session_state.tfvars_content,
            file_name=f"{sid}.tfvars",
            mime="text/plain",
            use_container_width=True
        )
    
    # Vorschau im Expander
    with col2:
        with st.expander("📄 Vorschau anzeigen"):
            st.code(st.session_state.tfvars_content, language="hcl")

# === SIDEBAR ===
with st.sidebar:
    st.subheader("🧠 Status")
    
    # Zeige aktuellen Block
    if st.session_state.messages:
        st.info(f"Gesprächsstatus: {'Abgeschlossen' if st.session_state.tfvars_ready else 'Laufend'}")
    
    if st.session_state.tfvars_ready:
        if st.button("🔄 Neu starten"):
            # State zurücksetzen
            st.session_state.messages = []
            st.session_state.tfvars_ready = False
            st.session_state.tfvars_content = ""
            requests.post("http://backend:8000/reset")
            st.rerun()
    else:
        st.info("🔄 Warte auf Eingabe...")