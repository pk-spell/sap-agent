"""
SAP Deployment Assistant - Chat Interface (v2 Refactored)
==========================================================

Clean, modular chat interface using component architecture.

Author: Claude Code
Date: 2025-11-20
"""

import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
from components.sidebar import render_sidebar
from api.client import BackendClient
from utils.helpers import extract_sid_from_content, generate_sdaf_filename

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="SAP Deployment Assistant",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://backend:8000")

# Initialize API client
api_client = BackendClient(API_URL)

# Elex Clerics Inspired Theme - Technical but neutral
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap');

    :root {
        /* Elex Clerics color palette - muted metallics */
        --bg-primary: #1a1d23;
        --bg-secondary: #252930;
        --bg-tertiary: #2e3238;
        --bg-card: #323640;

        /* Subtle tech accents - silver/steel tones */
        --accent-primary: #7a8591;
        --accent-secondary: #9da8b5;
        --accent-highlight: #b8c5d4;

        /* Text colors - readable grays */
        --text-primary: #d4dae0;
        --text-secondary: #8b95a1;
        --text-muted: #606873;

        /* Borders - subtle */
        --border-color: #3a3f47;
        --border-accent: #4a5059;
    }

    /* Main app background */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    /* Sidebar - cleaner look */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }

    /* Headers - subtle, not flashy */
    h1 {
        font-family: 'IBM Plex Mono', monospace !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
        font-size: 1.75rem !important;
    }

    h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: var(--accent-secondary) !important;
        font-weight: 500 !important;
    }

    /* Buttons - minimal design */
    .stButton > button {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-accent);
        border-radius: 3px;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 0.875rem;
        padding: 0.4rem 0.9rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: var(--bg-card);
        border-color: var(--accent-primary);
        color: var(--accent-highlight);
    }

    .stButton > button[kind="primary"] {
        background: var(--accent-primary);
        border: none;
        color: var(--bg-primary);
        font-weight: 500;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--accent-secondary);
    }

    /* Chat messages - clean cards */
    .stChatMessage {
        background: var(--bg-card);
        border-left: 2px solid var(--border-accent);
        border-radius: 4px;
        padding: 0.875rem;
        margin: 0.5rem 0;
    }

    /* User messages slightly different */
    .stChatMessage[data-testid="user-message"] {
        border-left-color: var(--accent-primary);
    }

    /* Download button */
    .stDownloadButton > button {
        background: var(--accent-primary);
        border: none;
        color: var(--bg-primary);
        font-weight: 500;
        font-family: 'IBM Plex Mono', monospace;
    }

    .stDownloadButton > button:hover {
        background: var(--accent-secondary);
    }

    /* Progress bar - subtle */
    .stProgress > div > div {
        background-color: var(--accent-primary);
    }

    /* Code blocks */
    code {
        background: var(--bg-tertiary);
        color: var(--accent-highlight);
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
    }

    /* Input fields */
    .stTextInput > div > div > input {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-accent);
        color: var(--text-primary);
    }

    /* Divider */
    hr {
        border-color: var(--border-color);
    }

    /* Sticky Progress Container */
    .stProgress {
        position: sticky;
        top: 0;
        z-index: 999;
        background: var(--bg-primary);
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state"""
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "sessions_list" not in st.session_state:
        st.session_state.sessions_list = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tfvars_ready" not in st.session_state:
        st.session_state.tfvars_ready = False
    if "tfvars_content" not in st.session_state:
        st.session_state.tfvars_content = ""
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    if "backend_online" not in st.session_state:
        st.session_state.backend_online = False
    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = 0
    if "show_preview_modal" not in st.session_state:
        st.session_state.show_preview_modal = False

# ============================================================================
# CALLBACKS
# ============================================================================

def handle_new_chat():
    """Create new chat session"""
    data = api_client.create_session()
    if data:
        st.session_state.current_session_id = data["session_id"]
        st.session_state.messages = [{"role": "assistant", "content": data.get("message", "Welcome!")}]
        st.session_state.tfvars_ready = False
        st.session_state.tfvars_content = ""
        st.session_state.current_prompt = data.get("current_prompt", 0)
        st.session_state.sessions_list = api_client.list_sessions()
        st.rerun()

def handle_switch_session(session_id: str):
    """Switch to existing session"""
    data = api_client.get_session(session_id)
    if data:
        st.session_state.current_session_id = session_id
        st.session_state.messages = data.get("messages", [])
        st.session_state.tfvars_ready = data.get("tfvars_ready", False)
        st.session_state.tfvars_content = data.get("tfvars_content", "")
        st.session_state.user_data = data.get("user_data", {})
        st.session_state.current_prompt = data.get("current_prompt", 0)
        st.rerun()

def handle_delete_session(session_id: str):
    """Delete session"""
    if api_client.delete_session(session_id):
        if st.session_state.current_session_id == session_id:
            st.session_state.current_session_id = None
            st.session_state.messages = []
            st.session_state.tfvars_ready = False
            st.session_state.tfvars_content = ""
        st.session_state.sessions_list = api_client.list_sessions()
        st.rerun()

def handle_user_message(user_input: str):
    """Handle user message submission"""
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})

    data = api_client.send_message(st.session_state.current_session_id, user_input)

    if data:
        st.session_state.messages.append({
            "role": "assistant",
            "content": data.get("message", "No response")
        })
        if "current_prompt" in data:
            st.session_state.current_prompt = data["current_prompt"]
        if data.get("tfvars_ready"):
            st.session_state.tfvars_ready = True
            st.session_state.tfvars_content = data.get("tfvars_content", "")
        if data.get("user_data"):
            st.session_state.user_data = data.get("user_data", {})
        st.rerun()
    else:
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()

# ============================================================================
# MAIN UI
# ============================================================================

def render_main_chat_area():
    """Render main chat interface"""

    # Header with title and progress bar
    header_col1, header_col2 = st.columns([4, 1])

    with header_col1:
        st.title("⚙️ SAP Deployment Assistant")

    with header_col2:
        # Small TFVARS Preview Button (only if session active and not complete)
        if st.session_state.current_session_id and st.session_state.messages and not st.session_state.tfvars_ready:
            if st.button("📄 Preview", key="preview_btn", help="Show TFVARS preview"):
                st.session_state.show_preview_modal = True

    # Progress bar (small, at top, only during conversation)
    if st.session_state.current_session_id and st.session_state.messages and not st.session_state.tfvars_ready:
        preview_data = api_client.get_preview(st.session_state.current_session_id)
        if preview_data:
            completion = preview_data.get("completion", 0)
            st.progress(completion / 100, text=f"Configuration Progress: {completion}%")
            st.divider()

    if not st.session_state.current_session_id:
        st.info("👈 Click **'➕ New Chat'** in the sidebar to start!")
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            ### Welcome to the SAP Deployment Assistant!

            1. Click **'➕ New Chat'** in the sidebar
            2. Answer questions using interactive forms or chat
            3. Download your generated tfvars file

            **Features:**
            - Interactive forms for key steps
            - Multiple sessions
            - Persistent history
            """)
        st.stop()

    # TFVARS Preview Modal (Popup Dialog)
    if hasattr(st.session_state, 'show_preview_modal') and st.session_state.show_preview_modal:
        preview_data = api_client.get_preview(st.session_state.current_session_id)
        if preview_data:
            preview_content = preview_data.get("preview", "")

            # Try using st.dialog (Streamlit 1.38+), fallback to expander
            try:
                @st.dialog("TFVARS Preview", width="large")
                def show_preview_dialog():
                    if preview_content:
                        st.code(preview_content, language="hcl", line_numbers=True)
                    else:
                        st.info("No preview available yet...")

                    if st.button("Close", type="primary", use_container_width=True):
                        st.session_state.show_preview_modal = False
                        st.rerun()

                show_preview_dialog()
            except AttributeError:
                # Fallback for older Streamlit versions
                st.markdown("---")
                st.subheader("📄 TFVARS Preview")
                if preview_content:
                    st.code(preview_content, language="hcl", line_numbers=True)
                else:
                    st.info("No preview available yet...")

                if st.button("✖ Close Preview", type="primary", use_container_width=True):
                    st.session_state.show_preview_modal = False
                    st.rerun()
                st.markdown("---")

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Download section
    if st.session_state.tfvars_ready and st.session_state.tfvars_content:
        st.divider()
        st.success("🎉 Your TFVARS file is ready!")

        # Generate SDAF-compliant filename
        if st.session_state.user_data:
            filename = generate_sdaf_filename(st.session_state.user_data)
        else:
            # Fallback to SID extraction
            sid = extract_sid_from_content(st.session_state.tfvars_content)
            filename = f"{sid}.tfvars"

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="📥 Download TFVARS File",
                data=st.session_state.tfvars_content,
                file_name=filename,
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        
        with st.expander("📄 Preview TFVARS Content"):
            st.code(st.session_state.tfvars_content, language="hcl")
        
        st.divider()

    # Chat input for all prompts
    if prompt := st.chat_input("Type your answer here...", key="chat_input"):
        handle_user_message(prompt)

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    init_session_state()
    
    st.session_state.backend_online = api_client.check_health()
    
    if st.session_state.backend_online:
        st.session_state.sessions_list = api_client.list_sessions()
        
        if st.session_state.current_session_id and not st.session_state.messages:
            data = api_client.get_session(st.session_state.current_session_id)
            if data:
                st.session_state.messages = data.get("messages", [])
                st.session_state.tfvars_ready = data.get("tfvars_ready", False)
                st.session_state.tfvars_content = data.get("tfvars_content", "")
                st.session_state.user_data = data.get("user_data", {})
                st.session_state.current_prompt = data.get("current_prompt", 0)

    render_sidebar(
        sessions_list=st.session_state.sessions_list,
        current_session_id=st.session_state.current_session_id,
        backend_online=st.session_state.backend_online,
        api_url=API_URL,
        on_new_chat=handle_new_chat,
        on_switch_session=handle_switch_session,
        on_delete_session=handle_delete_session
    )
    
    render_main_chat_area()

if __name__ == "__main__":
    main()
