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

# Custom CSS for better UI
st.markdown("""
<style>
    /* Reduce padding around main content */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Style session buttons */
    .stButton > button {
        width: 100%;
    }

    /* Make active session stand out */
    div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        margin-bottom: 0.5rem;
    }

    /* Download button styling */
    .download-section {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
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

    # Chat Input
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
