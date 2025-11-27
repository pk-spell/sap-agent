"""
SAP Deployment Automation Framework (SDAF) Chat Agent v2 - REFACTORED
=====================================================================

A session-based conversational agent that implements a 6-prompt flow for collecting
SAP deployment parameters and generating SDAF-compliant tfvars files.

This is the refactored version with modular architecture.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import uuid

# Modular imports
from config import DB_PATH
from models.session import ChatSession
from database.operations import (
    init_database,
    save_session_to_db,
    load_session_from_db,
    list_all_sessions,
    delete_session_from_db
)
from parsers import (
    parse_environment_input,
    parse_sap_system_input,
    parse_sizing_input,
    parse_architecture_input,
    parse_network_input,
    parse_os_input
)
from prompts import (
    get_prompt_message,
    is_greeting,
    get_greeting_response,
    generate_confirmation_summary,
    generate_final_summary,
    generate_sdaf_filename
)
from tfvars import generate_tfvars

# =============================================================================
# SETUP
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SDAF Chat Agent v2 (Refactored)", version="2.0.1")

# =============================================================================
# CONVERSATION HANDLER
# =============================================================================

async def process_user_message(session: ChatSession, user_message: str) -> str:
    """Process user message based on current prompt"""

    # GREETING DETECTION - respond friendly regardless of current prompt
    if is_greeting(user_message):
        return get_greeting_response()

    current_prompt = session.current_prompt

    # Prompt 0: Environment Identity - Progressive Questioning
    if current_prompt == 0:
        parsed = await parse_environment_input(user_message, session.user_data)

        # Check if parsing failed - show helpful error
        if not parsed and user_message.strip():
            from config import VALID_ENVIRONMENTS, AZURE_REGION_CODES
            env_list = ", ".join(VALID_ENVIRONMENTS[:8])
            region_list = ", ".join(list(AZURE_REGION_CODES.keys())[:8])
            return f"""I couldn't understand that input. Please provide valid SDAF environment information.

**Valid Environments:**
{env_list}, and more...

**Valid Azure Regions:**
{region_list}, and more...

**Network Name:**
- Max 7 characters, alphanumeric only

**Examples:**
- "DEV, westeurope, SAP01"
- "PROD / northeurope / SAP02"
- "QA in eastus network NET01"

Try again!"""

        # PROGRESSIVE: Merge with existing data (accumulate values across multiple inputs)
        for key, value in parsed.items():
            if value:  # Only update if value is not None/empty
                session.user_data[key] = value

        # Check what's still missing
        has_env = session.user_data.get("environment")
        has_location = session.user_data.get("location")
        has_network = session.user_data.get("network_logical_name")

        # ALL VALUES PRESENT → Proceed to next prompt
        if has_env and has_location and has_network:
            session.current_prompt = 1
            return get_prompt_message(1, session.user_data)

        # PARTIAL VALUES → Ask only for missing ones
        missing = []
        if not has_env:
            missing.append("**Environment** (DEV, PROD, QA, UAT, TEST, SBX, LAB, etc.)")
        if not has_location:
            missing.append("**Azure region** (westeurope, eastus, northeurope, etc.)")
        if not has_network:
            missing.append("**Network name** (max 7 chars, alphanumeric)")

        # Build dynamic response
        collected = []
        if has_env:
            collected.append(f"Environment: **{has_env}**")
        if has_location:
            collected.append(f"Region: **{has_location}**")
        if has_network:
            collected.append(f"Network: **{has_network}**")

        response = ""
        if collected:
            response += "Got it! " + ", ".join(collected) + "\n\n"

        response += f"I still need:\n" + "\n".join(f"{i+1}. {m}" for i, m in enumerate(missing))
        response += f"\n\n💡 You can provide them all at once or one at a time."

        return response

    # Prompt 1: SAP System Identity - Progressive Questioning
    elif current_prompt == 1:
        parsed = await parse_sap_system_input(user_message, session.user_data)

        # Check if parsing failed (empty dict usually means validation error)
        if not parsed and user_message.strip():
            # User provided input but parsing failed - likely invalid format
            return """I couldn't understand that input. Please provide valid SAP system information.

**Requirements:**
- **SID**: Exactly 3 characters, alphanumeric, must start with a letter
  - ✅ Valid: X00, P01, S15, HDB
  - ❌ Invalid: X, 00X, SAP (reserved), X_0 (special chars)
- **Database Platform**: HANA, DB2, ORACLE, ASE, SQLSERVER, or NONE

**Examples:**
- "X00, HDB, HANA"
- "P01 ORA ORACLE"
- "sid X00, db HDB, platform HANA"

Try again, or provide values one at a time!"""

        # PROGRESSIVE: Merge with existing data
        for key, value in parsed.items():
            if value:
                session.user_data[key] = value

        # Check what's still missing
        has_sid = session.user_data.get("sid")
        has_db_sid = session.user_data.get("database_sid")
        has_platform = session.user_data.get("database_platform")

        # ALL VALUES PRESENT → Proceed
        if has_sid and has_db_sid and has_platform:
            session.current_prompt = 2
            return get_prompt_message(2, session.user_data)

        # PARTIAL VALUES → Ask for missing
        missing = []
        if not has_sid:
            missing.append("**SAP Application SID** (3 chars, alphanumeric, starts with letter)")
        if not has_db_sid:
            missing.append("**Database SID** (3 chars, alphanumeric, starts with letter)")
        if not has_platform:
            missing.append("**Database platform** (HANA, DB2, ORACLE, ASE, SQLSERVER, NONE)")

        collected = []
        if has_sid:
            collected.append(f"App SID: **{has_sid}**")
        if has_db_sid:
            collected.append(f"DB SID: **{has_db_sid}**")
        if has_platform:
            collected.append(f"Platform: **{has_platform}**")

        response = ""
        if collected:
            response += "Perfect! " + ", ".join(collected) + "\n\n"

        response += "I still need:\n" + "\n".join(f"{i+1}. {m}" for i, m in enumerate(missing))
        response += "\n\n💡 Example: 'X00, HDB, HANA'"

        return response

    # Prompt 2: System Sizing
    elif current_prompt == 2:
        parsed = await parse_sizing_input(user_message)

        database_size = parsed.get("database_size", "Demo")
        purpose = parsed.get("purpose", "development")

        session.user_data["database_size"] = database_size
        session.user_data["app_tier_sizing_dictionary_key"] = parsed.get("app_tier_sizing", "Optimized")
        session.user_data["purpose"] = purpose
        session.user_data["size_description"] = database_size

        # AUTO-CONFIGURE: If Demo/Testing/Small sizing, skip architecture prompt and set defaults
        is_demo_or_small = any(keyword in database_size.lower() for keyword in ["demo", "s4demo"]) or \
                          any(keyword in purpose.lower() for keyword in ["demo", "test", "testing"])

        if is_demo_or_small:
            # Set standalone, no HA defaults
            session.user_data["enable_app_tier_deployment"] = False
            session.user_data["application_server_count"] = 0
            session.user_data["scs_server_count"] = 1
            session.user_data["database_server_count"] = 1
            session.user_data["database_high_availability"] = False
            session.user_data["scs_high_availability"] = False
            session.user_data["architecture_type"] = "standalone"
            session.user_data["ha_enabled"] = False

            # Skip Prompt 3 (Architecture) → Go directly to Prompt 4 (Network)
            session.current_prompt = 4
            return f"""Perfect! Since this is a **{purpose}** system with **{database_size}** sizing, I've automatically configured it as:

✅ **Standalone deployment** (everything on one server)
✅ **No High Availability** (single instance, cost-optimized)

This is the recommended setup for demo/testing/development environments.

{get_prompt_message(4, session.user_data)}"""

        else:
            # Normal flow: continue to Prompt 3 (Architecture)
            session.current_prompt = 3
            return get_prompt_message(3, session.user_data)

    # Prompt 3: Architecture Pattern
    elif current_prompt == 3:
        parsed = await parse_architecture_input(user_message)

        deployment_type = parsed.get("deployment_type", "standalone")
        ha_required = parsed.get("ha_required", False)
        app_count = parsed.get("application_server_count", 0)

        if deployment_type == "standalone":
            session.user_data["enable_app_tier_deployment"] = False
            session.user_data["application_server_count"] = 0
            session.user_data["scs_server_count"] = 1
            session.user_data["database_server_count"] = 1
            session.user_data["database_high_availability"] = False
            session.user_data["scs_high_availability"] = False
        else:  # distributed
            session.user_data["enable_app_tier_deployment"] = True
            session.user_data["application_server_count"] = app_count if app_count > 0 else 2

            if ha_required:
                session.user_data["scs_server_count"] = 2
                session.user_data["database_server_count"] = 2
                session.user_data["database_high_availability"] = True
                session.user_data["scs_high_availability"] = True
            else:
                session.user_data["scs_server_count"] = 1
                session.user_data["database_server_count"] = 1
                session.user_data["database_high_availability"] = False
                session.user_data["scs_high_availability"] = False

        session.user_data["architecture_type"] = deployment_type
        session.user_data["ha_enabled"] = ha_required

        session.current_prompt = 4
        return get_prompt_message(4, session.user_data)

    # Prompt 4: Network Configuration
    elif current_prompt == 4:
        parsed = await parse_network_input(user_message)

        session.user_data["network_type"] = parsed.get("network_type", "greenfield")

        if parsed.get("custom_cidrs"):
            session.user_data["admin_subnet"] = parsed.get("admin_subnet", "10.1.0.0/24")
            session.user_data["db_subnet"] = parsed.get("db_subnet", "10.1.1.0/24")
            session.user_data["app_subnet"] = parsed.get("app_subnet", "10.1.2.0/24")
            session.user_data["web_subnet"] = parsed.get("web_subnet", "10.1.3.0/24")
        else:
            # Use defaults
            session.user_data["admin_subnet"] = "10.1.0.0/24"
            session.user_data["db_subnet"] = "10.1.1.0/24"
            session.user_data["app_subnet"] = "10.1.2.0/24"
            session.user_data["web_subnet"] = "10.1.3.0/24"

        session.current_prompt = 5
        return get_prompt_message(5, session.user_data)

    # Prompt 5: Operating System
    elif current_prompt == 5:
        parsed = await parse_os_input(user_message)

        session.user_data["os_publisher"] = parsed.get("publisher", "SUSE")
        session.user_data["os_offer"] = parsed.get("offer", "sles-sap-15-sp5")
        session.user_data["os_sku"] = parsed.get("sku", "gen2")

        # Move to confirmation prompt
        session.current_prompt = 6
        return generate_confirmation_summary(session.user_data)

    # Prompt 6: Confirmation
    elif current_prompt == 6:
        user_input_lower = user_message.lower().strip()

        # Check for confirmation keywords
        if any(word in user_input_lower for word in ["ja", "yes", "confirm", "bestätigen", "korrekt", "richtig", "ok", "okay"]):
            # Generate tfvars
            session.tfvars_content = generate_tfvars(session.user_data)
            session.tfvars_ready = True
            session.current_prompt = 7

            filename = generate_sdaf_filename(session.user_data)
            return f"""✅ **Bestätigt!** Deine tfvars-Datei wird jetzt generiert...

📥 **Download bereit:** `{filename}`

Nutze den Download-Button unten um deine SDAF-konforme Konfigurationsdatei herunterzuladen!

💡 *Du kannst jetzt auch einen neuen Chat starten für eine andere Konfiguration.*
"""

        # Check for rejection/edit request
        elif any(word in user_input_lower for word in ["nein", "no", "ändern", "edit", "korrigieren", "falsch"]):
            return """Kein Problem! Was möchtest du ändern?

Sag mir einfach welcher Wert korrigiert werden soll, z.B.:
- "Ändere Environment auf PROD"
- "Region soll northeurope sein"
- "SID soll P01 sein"

Oder starte einen neuen Chat um komplett von vorne zu beginnen.
"""

        else:
            # Unclear response, ask again
            return """Bitte bestätige mit **"ja"** wenn alles korrekt ist, oder sage **"nein"** wenn du etwas ändern möchtest.

Du kannst auch direkt sagen was geändert werden soll, z.B. "Ändere SID auf P01"
"""

    else:
        return "Configuration is complete! You can download the tfvars file or start a new session."


# =============================================================================
# FASTAPI ENDPOINTS
# =============================================================================

class ChatRequest(BaseModel):
    message: str

class SessionResponse(BaseModel):
    session_id: str
    title: str
    current_prompt: int
    tfvars_ready: bool


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.0.1-refactored"}


@app.post("/sessions/new")
async def create_session():
    """Create a new chat session with welcome message"""
    try:
        session_id = str(uuid.uuid4())[:8]
        session = ChatSession(session_id)

        # Add welcome message
        welcome = get_prompt_message(0)
        session.add_message("assistant", welcome)

        # Save to database
        save_session_to_db(session)

        return {
            "session_id": session.session_id,
            "message": welcome,
            "current_prompt": 0,
            "tfvars_ready": False
        }
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all chat sessions"""
    try:
        sessions = list_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Load a specific session"""
    try:
        session = load_session_from_db(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session.session_id,
            "messages": session.messages,
            "current_prompt": session.current_prompt,
            "user_data": session.user_data,
            "tfvars_ready": session.tfvars_ready,
            "tfvars_content": session.tfvars_content,
            "title": session.get_title()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        success = delete_session_from_db(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"status": "deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    """Send a message in a session and get response"""
    try:
        # Load session
        session = load_session_from_db(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Add user message
        session.add_message("user", req.message)

        # Process message and get response
        response = await process_user_message(session, req.message)

        # Add assistant response
        session.add_message("assistant", response)

        # Save session
        save_session_to_db(session)

        return {
            "session_id": session.session_id,
            "message": response,
            "current_prompt": session.current_prompt,
            "tfvars_ready": session.tfvars_ready,
            "tfvars_content": session.tfvars_content if session.tfvars_ready else "",
            "user_data": session.user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/preview")
async def preview_tfvars(session_id: str):
    """Generate preview of TFVARS based on current user_data (even if incomplete)"""
    try:
        # Load session
        session = load_session_from_db(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Generate preview with current data (may be incomplete)
        preview_content = generate_tfvars(session.user_data)

        # Calculate completion percentage based on prompts (0-6)
        # Prompt 0: environment, location, network_logical_name (3 fields)
        # Prompt 1: sid, database_sid, database_platform (3 fields)
        # Prompt 2: sizing (1 field)
        # Prompt 3: architecture (optional)
        # Prompt 4: network (optional)
        # Prompt 5: os_selection (optional)

        total_prompts = 6
        completion = int((session.current_prompt / total_prompts) * 100)

        return {
            "session_id": session_id,
            "preview": preview_content,
            "completion": completion,
            "current_prompt": session.current_prompt,
            "user_data": session.user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
