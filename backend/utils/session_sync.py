"""
Session Synchronization - Agent V3 <-> ChatSession (SQLite)
============================================================

Helper functions to sync between:
- Agent V3's AgentState (in-memory)
- ChatSession (SQLite persistence from V2)
"""

from typing import Dict, Any
from models.session import ChatSession
from agent_v3 import AgentState


def agent_state_to_chat_session(session_id: str, agent_state: AgentState) -> ChatSession:
    """
    Convert AgentState to ChatSession for database storage

    Args:
        session_id: Session ID
        agent_state: Agent's current state

    Returns:
        ChatSession object ready for database
    """
    # Convert messages format
    # AgentState: List[Tuple[str, str]] → ChatSession: List[Dict[str, str]]
    messages = [
        {"role": role, "content": content}
        for role, content in agent_state.messages
    ]

    # Create ChatSession
    session = ChatSession(
        session_id=session_id,
        current_prompt=agent_state.current_step,
        user_data=agent_state.user_answers.copy(),
        messages=messages,
        tfvars_ready=agent_state.tfvars_ready,
        tfvars_content=agent_state.tfvars_content or ""
    )

    return session


def chat_session_to_agent_state(chat_session: ChatSession) -> AgentState:
    """
    Convert ChatSession (from database) to AgentState

    Args:
        chat_session: Session loaded from database

    Returns:
        AgentState object for Agent V3
    """
    state = AgentState()

    # Convert messages format
    # ChatSession: List[Dict[str, str]] → AgentState: List[Tuple[str, str]]
    state.messages = [
        (msg["role"], msg["content"])
        for msg in chat_session.messages
    ]

    # Copy other fields
    state.current_step = chat_session.current_prompt
    state.user_answers = chat_session.user_data.copy()
    state.tfvars_ready = chat_session.tfvars_ready
    state.tfvars_content = chat_session.tfvars_content

    return state


def merge_agent_state_into_session(agent_state: AgentState, chat_session: ChatSession):
    """
    Merge AgentState changes into existing ChatSession (in-place update)

    Use this to update an existing ChatSession with new agent state

    Args:
        agent_state: Current agent state
        chat_session: Existing session to update
    """
    # Update messages
    chat_session.messages = [
        {"role": role, "content": content}
        for role, content in agent_state.messages
    ]

    # Update other fields
    chat_session.current_prompt = agent_state.current_step
    chat_session.user_data = agent_state.user_answers.copy()
    chat_session.tfvars_ready = agent_state.tfvars_ready
    chat_session.tfvars_content = agent_state.tfvars_content or ""
