"""
FastAPI Backend V3 - Mit Agent V3 (LLM-Factory)
===============================================

Features:
- Agent V3 mit austauschbaren LLMs
- Session Management
- Chat History (SQLite)
- TFVARS Download
- Health Check

Run:
    python3 main_v3.py
    # oder
    uvicorn main_v3:app --reload --host 0.0.0.0 --port 8000
"""

import uuid
import json
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Agent V3 Hybrid (V2 Logic + V3 LLM-Factory)
from agent_v3_hybrid import get_agent, reset_agent

# Config
from config_loader import get_config

# Database (from V2)
from database.operations import (
    init_database,
    save_session_to_db,
    load_session_from_db,
    list_all_sessions,
    delete_session_from_db
)
from models.session import ChatSession

# Session Sync (AgentState <-> ChatSession)
from utils.session_sync import (
    agent_state_to_chat_session,
    chat_session_to_agent_state,
    merge_agent_state_into_session
)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and check LLM connection on startup"""
    print("🚀 Starting SAP Deployment Assistant V3...")

    # Initialize SQLite database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # Test LLM connection
    try:
        llm = config.get_llm("default")
        print(f"✅ LLM configured: {llm}")
    except Exception as e:
        print(f"⚠️  LLM configuration error: {e}")

    print("✅ Ready to accept requests!")

    yield

    # Shutdown (cleanup if needed)
    print("👋 Shutting down...")


# FastAPI App with lifespan
app = FastAPI(
    title="SAP Deployment Assistant V3",
    description="Conversational AI for SAP TFVARS generation - Local with LLM-Factory",
    version="3.0.0",
    lifespan=lifespan
)

# Load config
config = get_config()
cors_config = config.get_cors_config()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get("origins", ["http://localhost:5173"]),
    allow_credentials=True,
    allow_methods=cors_config.get("allow_methods", ["*"]),
    allow_headers=cors_config.get("allow_headers", ["*"]),
)


# Pydantic Models
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str  # Changed from 'response' to 'reply' to match frontend
    session_id: str
    tfvars_ready: bool = False
    current_step: int = 0
    total_steps: int = 6


class SessionCreate(BaseModel):
    name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    name: str
    created_at: str


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        llm = config.get_llm("default")
        llm_info = str(llm)
    except Exception as e:
        llm_info = f"Error: {e}"

    return {
        "status": "healthy",
        "version": "3.0.0",
        "llm": llm_info,
        "mode": "local",
        "timestamp": datetime.now().isoformat()
    }


# Session Management
@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session_data: Optional[SessionCreate] = None):
    """Create new chat session"""
    session_id = str(uuid.uuid4())[:8]  # Short ID wie in V2
    session_name = session_data.name if session_data else f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    created_at = datetime.now().isoformat()

    # Create agent and get welcome message
    agent = get_agent(session_id)
    welcome_message = await agent.get_welcome_message()

    # Add welcome message to agent state
    agent.state.add_message("assistant", welcome_message)

    # Convert AgentState → ChatSession
    chat_session = agent_state_to_chat_session(session_id, agent.state)

    # Save to database
    try:
        save_session_to_db(chat_session)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return SessionResponse(
        session_id=session_id,
        name=chat_session.get_title(),
        created_at=created_at
    )


@app.get("/api/sessions")
async def get_sessions():
    """List all sessions"""
    try:
        sessions = list_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get session details and messages"""
    try:
        chat_session = load_session_from_db(session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Return session data
        return {
            "session_id": chat_session.session_id,
            "name": chat_session.get_title(),
            "messages": chat_session.messages,
            "tfvars_ready": chat_session.tfvars_ready,
            "tfvars_content": chat_session.tfvars_content if chat_session.tfvars_ready else ""
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete session"""
    try:
        success = delete_session_from_db(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        # Also reset agent
        reset_agent(session_id)

        return {"message": "Session deleted", "status": "deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


# Chat Endpoints
@app.post("/api/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, msg: ChatMessage):
    """
    Chat endpoint - Main conversation

    Args:
        session_id: Session UUID
        msg: User message

    Returns:
        Agent response + TFVARS status
    """
    try:
        # Load session from database
        chat_session = load_session_from_db(session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get agent for session (creates new one if not in memory)
        agent = get_agent(session_id)

        # If agent state is empty, restore from database
        if not agent.state.messages and chat_session.messages:
            agent.state = chat_session_to_agent_state(chat_session)

        # Process message
        response = await agent.process_message(msg.message)

        # Convert AgentState → ChatSession and save
        updated_session = agent_state_to_chat_session(session_id, agent.state)
        save_session_to_db(updated_session)

        return ChatResponse(
            reply=response,
            session_id=session_id,
            tfvars_ready=agent.state.tfvars_ready,
            current_step=agent.state.current_step,
            total_steps=len(agent.state.steps)
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")


@app.get("/api/sessions/{session_id}/tfvars")
async def get_tfvars(session_id: str):
    """Get generated TFVARS content"""
    agent = get_agent(session_id)

    if not agent.state.tfvars_ready:
        raise HTTPException(status_code=400, detail="TFVARS not ready yet")

    tfvars_content = agent.get_tfvars()
    if not tfvars_content:
        raise HTTPException(status_code=404, detail="TFVARS not found")

    # Use SDAF-compliant filename
    filename = agent.get_tfvars_filename()

    return {
        "content": tfvars_content,
        "filename": filename
    }


@app.get("/api/sessions/{session_id}/tfvars/download")
async def download_tfvars(session_id: str):
    """Download TFVARS as file"""
    agent = get_agent(session_id)

    if not agent.state.tfvars_ready:
        raise HTTPException(status_code=400, detail="TFVARS not ready yet")

    tfvars_content = agent.get_tfvars()
    if not tfvars_content:
        raise HTTPException(status_code=404, detail="TFVARS not found")

    # Write to temp file
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tfvars')
    temp_file.write(tfvars_content)
    temp_file.close()

    # Use SDAF-compliant filename
    filename = agent.get_tfvars_filename()

    return FileResponse(
        temp_file.name,
        media_type="text/plain",
        filename=filename,
        background=lambda: os.unlink(temp_file.name)
    )


@app.post("/api/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset session (clear agent state)"""
    reset_agent(session_id)
    return {"message": "Session reset"}


# Config endpoint (for debugging)
@app.get("/api/config")
async def get_config_info():
    """Get current LLM configuration"""
    try:
        default_llm = config.get_llm("default")
        parsing_llm = config.get_llm("parsing")

        return {
            "default_llm": str(default_llm),
            "parsing_llm": str(parsing_llm),
            "config_loaded": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "config_loaded": False
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SAP Deployment Assistant V3",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    server_config = config.get_server_config()

    print("""
    ╔═══════════════════════════════════════════════════╗
    ║   SAP Deployment Assistant V3 - Local Edition    ║
    ║                                                   ║
    ║   Backend: FastAPI + Agent V3                    ║
    ║   LLM: Ollama (austauschbar!)                    ║
    ║   Kosten: €0                                     ║
    ╚═══════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main_v3:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", True)
    )
