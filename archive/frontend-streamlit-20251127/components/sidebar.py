"""
Sidebar Component - Session Management
======================================

Displays session list, allows creation, switching, and deletion of chat sessions.
"""

import streamlit as st
from typing import Dict, Any


def format_session_title(session: Dict[str, Any]) -> str:
    """
    Format session title for display

    Args:
        session: Session data dictionary

    Returns:
        str: Formatted title
    """
    title = session.get("title", "Untitled Chat")

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


def render_sidebar(
    sessions_list: list,
    current_session_id: str,
    backend_online: bool,
    api_url: str,
    on_new_chat,
    on_switch_session,
    on_delete_session
):
    """
    Render the sidebar with session management

    Args:
        sessions_list: List of session dictionaries
        current_session_id: Currently active session ID
        backend_online: Backend connection status
        api_url: Backend API URL
        on_new_chat: Callback for creating new chat
        on_switch_session: Callback for switching sessions
        on_delete_session: Callback for deleting sessions
    """
    with st.sidebar:
        st.title("💬 Chats")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            on_new_chat()

        st.divider()

        # Backend Status
        if backend_online:
            st.success("✅ Backend online")
        else:
            st.error("❌ Backend offline")
            st.warning("Please start the backend with:\n```\ndocker-compose up\n```")

        st.divider()

        # Session List
        st.subheader("Chat History")

        if sessions_list:
            for session in sessions_list:
                session_id = session["session_id"]
                is_active = session_id == current_session_id

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
                            on_switch_session(session_id)

                        # Subtitle with message count
                        st.caption(get_session_subtitle(session))

                    with col2:
                        # Delete button
                        if st.button(
                            "🗑️",
                            key=f"del_{session_id}",
                            help="Delete this chat"
                        ):
                            on_delete_session(session_id)

                    # Add spacing between sessions
                    st.write("")
        else:
            st.info("No chats yet.\nClick '➕ New Chat' to start!")

        # Footer with version info
        st.divider()
        st.caption("SAP Deployment Assistant v2.0")
        st.caption(f"API: {api_url}")
