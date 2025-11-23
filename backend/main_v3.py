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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Agent V3
from agent_v3 import get_agent, reset_agent

# Config
from config_loader import get_config

# Simple in-memory session storage for MVP
# TODO: Integrate V2 database later
_sessions_db: dict = {}

# FastAPI App
app = FastAPI(
    title="SAP Deployment Assistant V3",
    description="Conversational AI for SAP TFVARS generation - Local with LLM-Factory",
    version="3.0.0"
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
    response: str
    session_id: str
    tfvars_ready: bool = False


class SessionCreate(BaseModel):
    name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    name: str
    created_at: str


# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Check Ollama connection"""
    print("🚀 Starting SAP Deployment Assistant V3...")

    # Test LLM connection
    try:
        llm = config.get_llm("default")
        print(f"✅ LLM configured: {llm}")
    except Exception as e:
        print(f"⚠️  LLM configuration error: {e}")

    print("✅ Ready to accept requests!")


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
    session_id = str(uuid.uuid4())
    session_name = session_data.name if session_data else f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    created_at = datetime.now().isoformat()

    # Store in memory
    _sessions_db[session_id] = {
        "session_id": session_id,
        "name": session_name,
        "created_at": created_at,
        "messages": []
    }

    return SessionResponse(
        session_id=session_id,
        name=session_name,
        created_at=created_at
    )


@app.get("/api/sessions")
async def get_sessions():
    """List all sessions"""
    sessions = list(_sessions_db.values())
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get session details and messages"""
    session = _sessions_db.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete session"""
    if session_id not in _sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    del _sessions_db[session_id]

    # Also reset agent
    reset_agent(session_id)

    return {"message": "Session deleted"}


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
    # Check if session exists
    if session_id not in _sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get agent for session
    agent = get_agent(session_id)

    # Process message
    try:
        response = await agent.process_message(msg.message)

        # Save messages to session
        _sessions_db[session_id]["messages"].append({"role": "user", "content": msg.message})
        _sessions_db[session_id]["messages"].append({"role": "assistant", "content": response})

        return ChatResponse(
            response=response,
            session_id=session_id,
            tfvars_ready=agent.state.tfvars_ready
        )

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

    return {
        "content": tfvars_content,
        "filename": f"sap_{session_id[:8]}.tfvars"
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

    # Get SID from agent state
    sid = agent.state.user_answers.get("sap_system", {}).get("sid", session_id[:8])
    filename = f"sap_{sid}.tfvars"

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
