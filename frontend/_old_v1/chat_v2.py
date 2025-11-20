"""
SAP Deployment Assistant - Streamlit Frontend v2
================================================

This frontend implements a session-based chat interface that works with
the v2 backend API (backend/chat_agent_v2.py).

Features:
- Session management (create, switch, delete)
- Persistent chat history
- TFVARS download when ready
- Clean, professional UI
- Graceful error handling

Author: Claude Code
Date: 2025-11-16
"""

import streamlit as st
import requests
import re
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="SAP Deployment Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://backend:8000")

# Elex Clerics Inspired Tech Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');

    /* ===== COLOR PALETTE - Elex Clerics Tech Theme ===== */
    :root {
        --bg-primary: #0a0e1a;         /* Deep space blue-black */
        --bg-secondary: #151b2d;       /* Card backgrounds */
        --bg-tertiary: #1e2842;        /* Elevated elements */
        --accent-cyan: #00d9ff;        /* Primary tech glow */
        --accent-blue: #0066ff;        /* Secondary accent */
        --accent-purple: #8b5cf6;      /* Purple highlights */
        --text-primary: #e0e6ed;       /* Main text */
        --text-secondary: #8a95a8;     /* Muted text */
        --border: #2a3f5f;             /* Borders */
        --danger: #ff3b3b;             /* Delete/Error */
    }

    /* ===== MAIN APP BACKGROUND ===== */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f1420 50%, #0a0e1a 100%);
        font-family: 'Rajdhani', sans-serif;
        color: var(--text-primary);
    }

    /* ===== SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-right: 1px solid var(--border);
        box-shadow: 4px 0 20px rgba(0, 217, 255, 0.08);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* Sidebar Title */
    [data-testid="stSidebar"] h1 {
        font-family: 'Orbitron', monospace !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: var(--accent-cyan) !important;
        text-transform: uppercase;
        letter-spacing: 3px;
        border-bottom: 2px solid var(--accent-cyan);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
    }

    [data-testid="stSidebar"] h2 {
        font-family: 'Orbitron', monospace !important;
        font-size: 0.75rem !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* ===== MAIN CONTENT AREA ===== */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }

    /* Main Title */
    h1 {
        font-family: 'Orbitron', monospace !important;
        color: var(--accent-cyan) !important;
        text-shadow: 0 0 15px rgba(0, 217, 255, 0.4);
        font-weight: 900 !important;
        letter-spacing: 2px;
    }

    /* ===== BUTTONS - Tech Style ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
        border: 1px solid var(--border);
        border-radius: 4px;
        color: var(--text-primary);
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.4rem 0.8rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-cyan) 100%);
        border-color: var(--accent-cyan);
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
        transform: translateY(-2px);
        color: var(--bg-primary);
    }

    /* Primary Button (New Chat) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
        border: none;
        color: var(--bg-primary);
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0, 217, 255, 0.3);
    }

    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 25px rgba(0, 217, 255, 0.6);
        transform: translateY(-3px) scale(1.02);
    }

    /* Session List Buttons - Compact */
    .stButton > button[data-testid*="load_"] {
        font-size: 0.8rem;
        padding: 0.35rem 0.6rem;
        margin-bottom: 0.2rem;
    }

    /* Active Session Indicator */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    }

    /* Delete Buttons */
    .stButton > button:has-text("🗑") {
        background: rgba(255, 59, 59, 0.1);
        border-color: var(--danger);
        color: var(--danger);
        padding: 0.3rem 0.5rem;
        font-size: 0.85rem;
        min-width: 40px;
        width: auto !important;
    }

    .stButton > button:has-text("🗑"):hover {
        background: rgba(255, 59, 59, 0.3);
        box-shadow: 0 0 15px rgba(255, 59, 59, 0.5);
    }

    /* ===== CHAT MESSAGES ===== */
    .stChatMessage {
        background: var(--bg-tertiary);
        border-left: 3px solid var(--accent-cyan);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* User Message */
    .stChatMessage[data-testid*="user"] {
        border-left-color: var(--accent-purple);
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, rgba(139, 92, 246, 0.1) 100%);
    }

    /* Assistant Message */
    .stChatMessage[data-testid*="assistant"] {
        border-left-color: var(--accent-cyan);
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, rgba(0, 217, 255, 0.05) 100%);
    }

    /* ===== CHAT INPUT ===== */
    .stChatInputContainer {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 -2px 15px rgba(0, 217, 255, 0.1);
    }

    .stChatInputContainer textarea {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 0.95rem !important;
    }

    .stChatInputContainer textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.3) !important;
    }

    /* ===== DIVIDERS ===== */
    hr {
        border-color: var(--border);
        opacity: 0.5;
    }

    /* ===== TEXT STYLING ===== */
    p, li, span {
        color: var(--text-primary);
        font-family: 'Rajdhani', sans-serif;
    }

    strong, b {
        color: var(--accent-cyan);
        font-weight: 700;
    }

    /* ===== CODE BLOCKS ===== */
    code {
        background: var(--bg-secondary);
        color: var(--accent-cyan);
        border: 1px solid var(--border);
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }

    pre {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1rem;
    }

    /* ===== SUCCESS/INFO/WARNING MESSAGES ===== */
    .stSuccess {
        background: rgba(0, 217, 255, 0.1) !important;
        border-left: 4px solid var(--accent-cyan) !important;
        color: var(--text-primary) !important;
    }

    .stInfo {
        background: rgba(0, 102, 255, 0.1) !important;
        border-left: 4px solid var(--accent-blue) !important;
        color: var(--text-primary) !important;
    }

    .stWarning {
        background: rgba(255, 193, 7, 0.1) !important;
        border-left: 4px solid #ffc107 !important;
        color: var(--text-primary) !important;
    }

    .stError {
        background: rgba(255, 59, 59, 0.1) !important;
        border-left: 4px solid var(--danger) !important;
        color: var(--text-primary) !important;
    }

    /* ===== SPINNER/LOADING ===== */
    .stSpinner > div {
        border-color: var(--accent-cyan) transparent transparent transparent !important;
    }

    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
        border: none;
        color: var(--bg-primary);
        font-weight: 700;
        font-family: 'Orbitron', monospace;
        letter-spacing: 1px;
        box-shadow: 0 4px 20px rgba(0, 217, 255, 0.4);
        transition: all 0.3s ease;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 6px 30px rgba(0, 217, 255, 0.6);
        transform: translateY(-2px) scale(1.02);
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-radius: 6px;
        color: var(--accent-cyan);
        font-weight: 600;
    }

    .streamlit-expanderHeader:hover {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.2);
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-cyan);
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
    }

    /* ===== CAPTIONS (Session subtitles) ===== */
    .caption {
        color: var(--text-secondary) !important;
        font-size: 0.7rem !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    /* ===== COLUMNS ===== */
    [data-testid="column"] {
        gap: 0.5rem;
    }

    /* ===== VERSION INFO ===== */
    [data-testid="stSidebar"] .caption {
        color: var(--text-secondary);
        font-size: 0.65rem;
        font-family: 'Orbitron', monospace;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state variables"""
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
    if "backend_online" not in st.session_state:
        st.session_state.backend_online = False
    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = 0

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_backend_health() -> bool:
    """
    Check if backend is reachable and healthy

    Returns:
        bool: True if backend is online, False otherwise
    """
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.ok
    except requests.exceptions.RequestException:
        return False

def extract_sid_from_content(tfvars: str) -> str:
    """
    Extract SID from tfvars content for filename

    Args:
        tfvars: The tfvars file content

    Returns:
        str: Extracted SID or "config" as fallback
    """
    # Try to find sid = "XXX" pattern
    match = re.search(r'sid\s*=\s*"(\w+)"', tfvars)
    if match:
        return match.group(1)

    # Fallback to timestamp-based name
    return f"sap_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def format_session_title(session: Dict[str, Any]) -> str:
    """
    Format session title for display

    Args:
        session: Session data dictionary

    Returns:
        str: Formatted title
    """
    title = session.get("title", "Untitled Chat")
    created_at = session.get("created_at", "")

    # If title is too long, truncate it
    if len(title) > 30:
        title = title[:27] + "..."

    return title

def get_session_subtitle(session: Dict[str, Any]) -> str:
    """
    Get session subtitle (timestamp or message count)

    Args:
        session: Session data dictionary

    Returns:
        str: Formatted subtitle
    """
    message_count = session.get("message_count", 0)
    if message_count > 0:
        return f"{message_count} messages"
    else:
        return "New chat"

# ============================================================================
# API INTERACTION FUNCTIONS
# ============================================================================

def create_new_session() -> bool:
    """
    Create a new chat session via API

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with st.spinner("Creating new chat session..."):
            response = requests.post(f"{API_URL}/sessions/new", timeout=10)
            response.raise_for_status()
            data = response.json()

            session_id = data["session_id"]
            welcome_message = data.get("message", data.get("welcome_message", "Welcome!"))

            # Set as active session
            st.session_state.current_session_id = session_id
            st.session_state.messages = [{"role": "assistant", "content": welcome_message}]
            st.session_state.tfvars_ready = False
            st.session_state.tfvars_content = ""
            st.session_state.current_prompt = data.get("current_prompt", 0)

            # Refresh session list
            load_sessions_list()

            return True

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to create session: {str(e)}")
        return False

def load_sessions_list() -> bool:
    """
    Load list of all sessions from API

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.get(f"{API_URL}/sessions", timeout=5)
        response.raise_for_status()
        data = response.json()

        st.session_state.sessions_list = data.get("sessions", [])
        return True

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load sessions: {str(e)}")
        return False

def switch_to_session(session_id: str) -> bool:
    """
    Switch to an existing session and load its full state

    Args:
        session_id: The session ID to switch to

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with st.spinner("Loading session..."):
            response = requests.get(f"{API_URL}/sessions/{session_id}", timeout=5)
            response.raise_for_status()
            data = response.json()

            # Update session state
            st.session_state.current_session_id = session_id
            st.session_state.messages = data.get("messages", [])
            st.session_state.tfvars_ready = data.get("tfvars_ready", False)
            st.session_state.tfvars_content = data.get("tfvars_content", "")
            st.session_state.current_prompt = data.get("current_prompt", 0)

            return True

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load session: {str(e)}")
        return False

def delete_session(session_id: str) -> bool:
    """
    Delete a session via API

    Args:
        session_id: The session ID to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with st.spinner("Deleting session..."):
            response = requests.delete(f"{API_URL}/sessions/{session_id}", timeout=5)
            response.raise_for_status()

            # If it was the active session, clear it
            if st.session_state.current_session_id == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
                st.session_state.tfvars_ready = False
                st.session_state.tfvars_content = ""

            # Refresh session list
            load_sessions_list()

            return True

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to delete session: {str(e)}")
        return False

def send_message(user_input: str) -> bool:
    """
    Send a message to the active session and get LLM response

    Args:
        user_input: The user's message

    Returns:
        bool: True if successful, False otherwise
    """
    if not st.session_state.current_session_id:
        st.error("No active session! Create a new chat first.")
        return False

    session_id = st.session_state.current_session_id

    # Add user message to UI immediately
    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        # Show thinking indicator
        with st.spinner("Assistant is thinking..."):
            response = requests.post(
                f"{API_URL}/sessions/{session_id}/chat",
                json={"message": user_input},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Add assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": data.get("message", data.get("assistant_message", "No response"))
            })

            # Update current prompt number
            if "current_prompt" in data:
                st.session_state.current_prompt = data["current_prompt"]

            # Update tfvars if ready
            if data.get("tfvars_ready"):
                st.session_state.tfvars_ready = True
                st.session_state.tfvars_content = data.get("tfvars_content", "")

            return True

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send message: {str(e)}")
        # Remove the user message we added optimistically
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
        return False

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_environment_form() -> Optional[str]:
    """
    Render interactive form for Prompt 0 (Environment selection)

    Returns:
        Optional[str]: Formatted message to send to backend, or None if not submitted
    """
    st.markdown("### 🌍 Environment Configuration")
    st.markdown("Please provide the following information:")

    with st.form(key="environment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            environment = st.selectbox(
                "Environment Type",
                options=["DEV", "PROD", "QA", "UAT", "TEST", "NONPROD", "SANDBOX"],
                index=0,
                help="Select the environment type for your SAP deployment"
            )

            location = st.selectbox(
                "Azure Region",
                options=[
                    "westeurope", "northeurope", "germanywestcentral",
                    "eastus", "eastus2", "westus", "westus2", "centralus",
                    "uksouth", "francecentral", "switzerlandnorth", "norwayeast"
                ],
                index=0,
                help="Select the Azure region where you want to deploy"
            )

        with col2:
            network_name = st.text_input(
                "Network Name",
                value="SAP01",
                max_chars=7,
                help="Short identifier for your network (max 7 characters)"
            )

            st.markdown("---")
            submit_button = st.form_submit_button("✅ Continue", use_container_width=True, type="primary")

        if submit_button:
            # Validate network name
            if not network_name or len(network_name) > 7:
                st.error("Network name must be 1-7 characters")
                return None

            # Format message for backend
            message = f"{environment}, {location}, {network_name}"
            return message

    return None

def render_sap_system_form() -> Optional[str]:
    """
    Render interactive form for Prompt 1 (SAP System identity)

    Returns:
        Optional[str]: Formatted message to send to backend, or None if not submitted
    """
    st.markdown("### 💾 SAP System Identification")
    st.markdown("Please identify your SAP system:")

    with st.form(key="sap_system_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            sap_sid = st.text_input(
                "SAP Application SID",
                value="X00",
                max_chars=3,
                help="3-character SAP Application SID (e.g., X00, P01, S15)"
            ).upper()

            db_sid = st.text_input(
                "Database SID",
                value="HDB",
                max_chars=3,
                help="3-character Database SID (e.g., HDB, XDB, ORA)"
            ).upper()

        with col2:
            db_platform = st.selectbox(
                "Database Platform",
                options=["HANA", "DB2", "ORACLE", "ASE", "SQLSERVER", "NONE"],
                index=0,
                help="Select the database platform for your SAP system"
            )

            st.markdown("---")
            submit_button = st.form_submit_button("✅ Continue", use_container_width=True, type="primary")

        if submit_button:
            # Validate SIDs
            if not sap_sid or len(sap_sid) != 3:
                st.error("SAP SID must be exactly 3 characters")
                return None
            if not db_sid or len(db_sid) != 3:
                st.error("Database SID must be exactly 3 characters")
                return None

            # Format message for backend
            message = f"{sap_sid}, {db_sid}, {db_platform}"
            return message

    return None

def render_sidebar():
    """Render the sidebar with session management"""
    with st.sidebar:
        st.title("💬 Chats")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            if create_new_session():
                st.rerun()

        st.divider()

        # Backend Status
        if st.session_state.backend_online:
            st.success("✅ Backend online")
        else:
            st.error("❌ Backend offline")
            st.warning("Please start the backend with:\n```\ndocker-compose up\n```")

        st.divider()

        # Session List
        st.subheader("Chat History")

        if st.session_state.sessions_list:
            for session in st.session_state.sessions_list:
                session_id = session["session_id"]
                is_active = session_id == st.session_state.current_session_id

                # Container for each session
                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        # Session title button
                        icon = "🔵" if is_active else "⚪"
                        title = format_session_title(session)
                        button_type = "primary" if is_active else "secondary"

                        if st.button(
                            f"{icon} {title}",
                            key=f"load_{session_id}",
                            use_container_width=True,
                            type=button_type if is_active else "secondary",
                            disabled=is_active
                        ):
                            if switch_to_session(session_id):
                                st.rerun()

                        # Subtitle with message count
                        st.caption(get_session_subtitle(session))

                    with col2:
                        # Delete button
                        if st.button(
                            "🗑️",
                            key=f"del_{session_id}",
                            help="Delete this chat"
                        ):
                            if delete_session(session_id):
                                st.rerun()

                    # Add spacing between sessions
                    st.write("")
        else:
            st.info("No chats yet.\nClick '➕ New Chat' to start!")

        # Footer with version info
        st.divider()
        st.caption("SAP Deployment Assistant v2.0")
        st.caption(f"API: {API_URL}")

def render_main_chat_area():
    """Render the main chat area"""

    # Header
    st.title("🤖 SAP Deployment Assistant")

    # DEBUG: Show current state at the very top
    st.error(f"🔍 DEBUG: current_prompt = {st.session_state.current_prompt}, session_id = {st.session_state.current_session_id}")

    # Check if there's an active session
    if not st.session_state.current_session_id:
        # Empty state
        st.info("👈 Click **'➕ New Chat'** in the sidebar to start a conversation!")

        # Optional: Show some help text
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            ### Welcome to the SAP Deployment Assistant!

            This tool helps you generate Terraform variable files (tfvars) for SAP deployments.

            **How it works:**
            1. Click **'➕ New Chat'** in the sidebar
            2. Answer the assistant's questions about your SAP deployment
            3. The assistant will gather information about:
               - Environment type (DEV, QA, PRD)
               - Azure region
               - SID (System ID)
               - Network configuration
               - VM sizes and other parameters
            4. Once complete, download your generated tfvars file

            **Features:**
            - Multiple chat sessions
            - Persistent conversation history
            - Session management (switch, delete)
            - Download generated configurations
            """)

        st.stop()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Download TFVARS section (if ready)
    if st.session_state.tfvars_ready and st.session_state.tfvars_content:
        st.divider()

        # Success message
        st.success("🎉 Your TFVARS file is ready!")

        # Extract SID for filename
        sid = extract_sid_from_content(st.session_state.tfvars_content)
        filename = f"{sid}.tfvars"

        # Download button in a prominent position
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

        # Preview in expander
        with st.expander("📄 Preview TFVARS Content"):
            st.code(st.session_state.tfvars_content, language="hcl")

        st.divider()

    # Smart Input: Show interactive forms for Prompt 0 and 1, otherwise use chat input
    current_prompt = st.session_state.current_prompt

    # PROMPT 0: Environment Configuration (Interactive Form)
    if current_prompt == 0:
        st.divider()
        user_input = render_environment_form()
        if user_input:
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            # Send to backend
            if send_message(user_input):
                st.rerun()

    # PROMPT 1: SAP System Identification (Interactive Form)
    elif current_prompt == 1:
        st.divider()
        user_input = render_sap_system_form()
        if user_input:
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            # Send to backend
            if send_message(user_input):
                st.rerun()

    # PROMPTS 2-6: Regular chat input
    else:
        if prompt := st.chat_input("Type your answer here...", key="chat_input"):
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(prompt)

            # Send to backend and get response
            if send_message(prompt):
                st.rerun()

# ============================================================================
# INITIALIZATION AND MAIN
# ============================================================================

def init_app():
    """Initialize the application on startup"""

    # Initialize session state
    init_session_state()

    # Check backend health
    st.session_state.backend_online = check_backend_health()

    if not st.session_state.backend_online:
        # Still show UI but with warning
        return

    # Load session list
    load_sessions_list()

    # If there's a current session ID but no messages loaded, load them
    if st.session_state.current_session_id and not st.session_state.messages:
        switch_to_session(st.session_state.current_session_id)

def main():
    """Main application entry point"""

    # Run initialization
    init_app()

    # Render UI components
    render_sidebar()
    render_main_chat_area()

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
