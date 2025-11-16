"""
SAP Deployment Automation Framework (SDAF) Chat Agent v2
==========================================================

A session-based conversational agent that implements a 6-prompt flow for collecting
SAP deployment parameters and generating SDAF-compliant tfvars files.

Key Features:
- Session-based architecture (no global state)
- LLM-driven natural language parsing
- 6-prompt conversational flow based on SDAF research
- SQLite persistence with full chat history
- Automatic tfvars generation with 180+ defaults
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from typing import Dict, Any, List, Optional
import logging
import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml
import re

# =============================================================================
# SETUP & CONFIGURATION
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SDAF Chat Agent v2", version="2.0.0")

# LLM Configuration
llm = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434",
    temperature=0.3  # Lower temperature for more consistent parsing
)

# Template Configuration
TEMPLATES_DIR = Path("/app/templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Database Configuration
DB_PATH = Path("/app/data/chat_sessions_v2.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# =============================================================================
# SESSION CLASS - Core State Management
# =============================================================================

class ChatSession:
    """Represents a single chat session with full state"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, str]] = []  # [{"role": "user/assistant", "content": "..."}]
        self.current_prompt = 0  # Which of the 6 prompts we're on (0-5)
        self.user_data: Dict[str, Any] = {}  # Collected parameters
        self.tfvars_ready = False
        self.tfvars_content = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.now()

    def get_title(self) -> str:
        """Generate a session title from collected data"""
        if self.user_data.get("sid") and self.user_data.get("location"):
            sid = self.user_data.get("sid", "")
            env = self.user_data.get("environment", "")
            location = self.user_data.get("location", "")
            return f"SAP {sid} - {env} - {location}"
        elif self.user_data.get("environment"):
            return f"SAP Config - {self.user_data.get('environment')}"
        else:
            return f"Chat - {self.created_at.strftime('%H:%M')}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary"""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "current_prompt": self.current_prompt,
            "user_data": self.user_data,
            "tfvars_ready": self.tfvars_ready,
            "tfvars_content": self.tfvars_content,
            "title": self.get_title(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        """Deserialize session from dictionary"""
        session = cls(data["session_id"])
        session.messages = data.get("messages", [])
        session.current_prompt = data.get("current_prompt", 0)
        session.user_data = data.get("user_data", {})
        session.tfvars_ready = data.get("tfvars_ready", False)
        session.tfvars_content = data.get("tfvars_content", "")

        # Parse datetime strings
        if isinstance(data.get("created_at"), str):
            session.created_at = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            session.updated_at = datetime.fromisoformat(data["updated_at"])

        return session

# =============================================================================
# DATABASE LAYER
# =============================================================================

def init_database():
    """Initialize SQLite database with schema"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                current_prompt INTEGER DEFAULT 0,
                user_data TEXT,
                tfvars_content TEXT,
                tfvars_ready BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def save_session_to_db(session: ChatSession):
    """Persist session to database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Save session metadata
        cursor.execute("""
            INSERT OR REPLACE INTO chat_sessions
            (session_id, title, current_prompt, user_data, tfvars_content, tfvars_ready, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.session_id,
            session.get_title(),
            session.current_prompt,
            json.dumps(session.user_data),
            session.tfvars_content,
            session.tfvars_ready,
            session.created_at,
            session.updated_at
        ))

        # Delete old messages for this session
        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session.session_id,))

        # Save all messages
        for msg in session.messages:
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content)
                VALUES (?, ?, ?)
            """, (session.session_id, msg["role"], msg["content"]))

        conn.commit()
        conn.close()
        logger.info(f"✅ Session {session.session_id} saved to database")
    except Exception as e:
        logger.error(f"❌ Failed to save session {session.session_id}: {e}")
        raise

def load_session_from_db(session_id: str) -> Optional[ChatSession]:
    """Load session from database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Load session metadata
        cursor.execute("""
            SELECT title, current_prompt, user_data, tfvars_content, tfvars_ready, created_at, updated_at
            FROM chat_sessions WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Create session object
        session = ChatSession(session_id)
        session.current_prompt = row[1]
        session.user_data = json.loads(row[2] or "{}")
        session.tfvars_content = row[3] or ""
        session.tfvars_ready = bool(row[4])
        session.created_at = datetime.fromisoformat(row[5])
        session.updated_at = datetime.fromisoformat(row[6])

        # Load messages
        cursor.execute("""
            SELECT role, content FROM chat_messages
            WHERE session_id = ? ORDER BY timestamp ASC
        """, (session_id,))

        session.messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

        conn.close()
        logger.info(f"✅ Session {session_id} loaded from database")
        return session
    except Exception as e:
        logger.error(f"❌ Failed to load session {session_id}: {e}")
        return None

def list_all_sessions() -> List[Dict[str, Any]]:
    """List all sessions with metadata"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, title, current_prompt, tfvars_ready, created_at, updated_at
            FROM chat_sessions ORDER BY updated_at DESC
        """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "title": row[1],
                "current_prompt": row[2],
                "tfvars_ready": bool(row[3]),
                "created_at": row[4],
                "updated_at": row[5]
            })

        conn.close()
        return sessions
    except Exception as e:
        logger.error(f"❌ Failed to list sessions: {e}")
        return []

def delete_session_from_db(session_id: str) -> bool:
    """Delete a session from database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        logger.info(f"✅ Session {session_id} deleted")
        return deleted
    except Exception as e:
        logger.error(f"❌ Failed to delete session {session_id}: {e}")
        return False

# =============================================================================
# PROMPT DEFINITIONS - 6-Prompt Conversational Flow
# =============================================================================

def get_prompt_message(prompt_num: int, context: Dict[str, Any] = None) -> str:
    """Get the message for each of the 6 prompts"""
    context = context or {}

    if prompt_num == 0:
        # Prompt 0: Welcome + Environment Identity
        return """Hi! I'll help you create an SAP deployment configuration. Let's start with the basics about your environment.

**First, I need to know three things:**

1. What environment is this? (e.g., DEV, PROD, QA, NONPROD)
2. Which Azure region? (e.g., westeurope, eastus, northeurope)
3. What should we call your network? (This is a short identifier, max 7 characters, like SAP01 or SAP02)

You can answer in any format you like - just tell me these three things!

**Examples:**
- "This is DEV in westeurope, network name SAP01"
- "production, east us, network SAP02"
- "dev / west europe / sap01"
"""

    elif prompt_num == 1:
        # Prompt 1: SAP System Identity
        env = context.get("environment", "")
        location = context.get("location", "")
        network = context.get("network_logical_name", "")

        return f"""Great! So we're setting up a **{env}** environment in **{location}** with network **{network}**.

**Now, let's identify your SAP system:**

1. What's the SAP Application SID? (3 characters, like X00, S15, P01)
2. What's the Database SID? (usually 3 characters, like HDB, XDB, ORA)
3. Which database platform are you using?
   - HANA (SAP HANA)
   - DB2 (IBM DB2)
   - ORACLE (Oracle Database)
   - ASE (SAP ASE/Sybase)
   - SQLSERVER (Microsoft SQL Server)
   - NONE (no database tier)

**Examples:**
- "SID is X00, database HDB, using HANA"
- "app sid: P01, db sid: ORA, oracle database"
- "X00 / HDB / HANA"
"""

    elif prompt_num == 2:
        # Prompt 2: System Sizing
        sid = context.get("sid", "")
        platform = context.get("database_platform", "")
        db_sid = context.get("database_sid", "")

        return f"""Perfect! We're deploying SAP **{sid}** with **{platform}** database (**{db_sid}**).

**Now let's talk about sizing. I need to understand how big this system needs to be:**

1. What's the primary purpose?
   - Demo/Testing (small, cost-optimized)
   - Development (small to medium)
   - QA/Staging (medium)
   - Production (medium to large)
   - Production with high load (large to extra-large)

2. For the database, what size do you need?
   - **Demo**: 32 GB memory (Standard_D8s_v3)
   - **Small**: 160-256 GB memory (E20ds_v4 or E32ds_v4)
   - **Medium**: 256-512 GB memory (E32ds_v4 or E64ds_v4)
   - **Large**: 512 GB - 1 TB memory (E64ds_v5 or M64s)
   - **XLarge**: 1-4 TB memory (M128s or M128ms)
   - **XXLarge**: 4+ TB memory (M208ms_v2 or larger)

Just tell me what you're aiming for, and I'll pick the right VM size!

**Examples:**
- "This is for development, medium size should be fine"
- "Production system, need large, around 1TB memory"
- "Demo environment, keep it small"
"""

    elif prompt_num == 3:
        # Prompt 3: Architecture Pattern
        purpose = context.get("purpose", "workload")
        size_desc = context.get("size_description", "")

        return f"""Got it - we'll size this for a **{purpose}** workload with **{size_desc}**.

**Now, let's decide on the architecture:**

1. **Deployment Type:**
   - **Standalone**: Everything on one server (simplest, good for dev/test)
   - **Distributed**: Separate servers for database, central services, and app servers (recommended for production)

2. **High Availability:**
   - Do you need HA/clustering for zero downtime? (yes/no)
   - Note: HA requires at least 2 servers for both database and central services

3. **Application Servers:**
   - If you choose Distributed, how many application servers do you need? (typically 1-4 for most systems)

**Examples:**
- "Standalone, no HA needed, this is just dev"
- "Distributed with 2 app servers, yes we need HA"
- "Distributed, 3 app servers, no HA for now"
"""

    elif prompt_num == 4:
        # Prompt 4: Network Configuration
        arch_type = context.get("architecture_type", "deployment")
        ha_statement = " with HA enabled" if context.get("ha_enabled") else ""

        return f"""Excellent! We're going with a **{arch_type}** architecture{ha_statement}.

**Now for the network setup - this is important:**

**Are you deploying into:**
1. **Greenfield** - A new virtual network that SDAF will create for you
2. **Brownfield** - An existing virtual network that's already set up

**If Greenfield (recommended for new deployments):**
I'll create a new VNet with four subnets using these default address ranges:
- Admin subnet: 10.1.0.0/24
- Database subnet: 10.1.1.0/24
- Application subnet: 10.1.2.0/24
- Web subnet: 10.1.3.0/24

You can customize these or accept the defaults.

**If Brownfield (using existing network):**
I'll need the Azure Resource IDs for your existing subnets.

What would you like to do?

**Examples:**
- "Greenfield please, defaults are fine"
- "Greenfield but use 10.10.x.x range"
- "Brownfield - I have the subnet IDs"
"""

    elif prompt_num == 5:
        # Prompt 5: Operating System
        return """Almost done! Last question - which operating system would you like to use?

**SDAF supports these SAP-certified OS options:**

**SUSE Linux Enterprise Server (SLES):**
- SLES 15 SP5 (latest, recommended)
- SLES 15 SP4
- SLES 15 SP3
- SLES 12 SP5

**Red Hat Enterprise Linux (RHEL):**
- RHEL 9.x (latest)
- RHEL 8.x (8.6, 8.4, 8.2)
- RHEL 7.x

Just tell me your preference - I'll configure the right image for all VMs (database, SCS, app servers).

**Examples:**
- "SUSE latest" → SLES 15 SP5
- "Red Hat 8" → RHEL 8.6
- "SLES 15 SP5" → SLES 15 SP5
- "RHEL 9" → RHEL 9.x
"""

    else:
        return "Invalid prompt number"

# =============================================================================
# LLM PARSING FUNCTIONS - Natural Language Understanding
# =============================================================================

async def parse_environment_input(user_message: str) -> Dict[str, Any]:
    """Parse free-form environment input using LLM"""
    prompt = f"""Extract SAP deployment parameters from this user input:
"{user_message}"

Expected parameters:
- environment: DEV/PROD/QA/NONPROD/etc (normalize to uppercase, max 5 chars)
- location: Azure region (westeurope, eastus, northeurope, etc)
- network_logical_name: Network identifier (max 7 chars, uppercase)

Return ONLY a valid JSON object like:
{{"environment": "DEV", "location": "westeurope", "network_logical_name": "SAP01"}}

If you cannot extract a parameter, use null.
"""

    try:
        response = await llm.ainvoke(prompt)
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except Exception as e:
        logger.error(f"Failed to parse environment input: {e}")
        return {}

async def parse_sap_system_input(user_message: str) -> Dict[str, Any]:
    """Parse SAP system identity from user input"""
    prompt = f"""Extract SAP system parameters from this user input:
"{user_message}"

Expected parameters:
- sid: SAP Application SID (3 uppercase chars, like X00, P01)
- database_sid: Database SID (3 chars, like HDB, XDB, ORA)
- database_platform: Database type (must be one of: HANA, DB2, ORACLE, ASE, SQLSERVER, NONE)

Return ONLY a valid JSON object like:
{{"sid": "X00", "database_sid": "HDB", "database_platform": "HANA"}}

If you cannot extract a parameter, use null.
"""

    try:
        response = await llm.ainvoke(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except Exception as e:
        logger.error(f"Failed to parse SAP system input: {e}")
        return {}

async def parse_sizing_input(user_message: str) -> Dict[str, Any]:
    """Parse sizing requirements from user input"""
    prompt = f"""Extract sizing information from this user input:
"{user_message}"

Expected information:
- purpose: demo/testing/development/qa/staging/production/high-load (normalize to lowercase)
- size_intent: demo/small/medium/large/xlarge/xxlarge
- memory_requirement: If mentioned, extract GB amount (e.g., "1TB" → 1024)

Map the intent to SDAF database_size keys:
- demo/testing → "Demo" or "S4Demo"
- small/development → "E20ds_v4" or "E32ds_v4"
- medium/qa → "E48ds_v4" or "E64ds_v4"
- large/production/512GB-1TB → "M64s" or "M64ls"
- xlarge/1-4TB → "M128s" or "M128ms"
- xxlarge/4TB+ → "M208ms_v2"

Return ONLY a valid JSON object like:
{{"purpose": "development", "database_size": "E32ds_v4", "app_tier_sizing": "Optimized"}}

If you cannot determine values, use sensible defaults.
"""

    try:
        response = await llm.ainvoke(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}
    except Exception as e:
        logger.error(f"Failed to parse sizing input: {e}")
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}

async def parse_architecture_input(user_message: str) -> Dict[str, Any]:
    """Parse architecture pattern from user input"""
    prompt = f"""Extract architecture decisions from this user input:
"{user_message}"

Expected parameters:
- deployment_type: "standalone" or "distributed"
- ha_required: true or false (high availability/clustering)
- application_server_count: integer (0 for standalone, 1-10 for distributed)

Logic:
- Standalone means everything on one VM (app_server_count = 0)
- Distributed means separate VMs (app_server_count >= 1)
- HA requires at least 2 servers for DB and SCS

Return ONLY a valid JSON object like:
{{"deployment_type": "distributed", "ha_required": false, "application_server_count": 2}}
"""

    try:
        response = await llm.ainvoke(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}
    except Exception as e:
        logger.error(f"Failed to parse architecture input: {e}")
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}

async def parse_network_input(user_message: str) -> Dict[str, Any]:
    """Parse network configuration from user input"""
    prompt = f"""Extract network configuration from this user input:
"{user_message}"

Expected parameters:
- network_type: "greenfield" or "brownfield"
- custom_cidrs: true/false (if user wants custom subnet CIDRs)
- admin_subnet: CIDR if custom (e.g., "10.10.0.0/24")
- db_subnet: CIDR if custom
- app_subnet: CIDR if custom
- web_subnet: CIDR if custom

Return ONLY a valid JSON object like:
{{"network_type": "greenfield", "custom_cidrs": false}}

or if custom:
{{"network_type": "greenfield", "custom_cidrs": true, "admin_subnet": "10.10.0.0/24", "db_subnet": "10.10.1.0/24", "app_subnet": "10.10.2.0/24", "web_subnet": "10.10.3.0/24"}}
"""

    try:
        response = await llm.ainvoke(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"network_type": "greenfield", "custom_cidrs": False}
    except Exception as e:
        logger.error(f"Failed to parse network input: {e}")
        return {"network_type": "greenfield", "custom_cidrs": False}

async def parse_os_input(user_message: str) -> Dict[str, Any]:
    """Parse operating system selection from user input"""
    prompt = f"""Extract OS selection from this user input:
"{user_message}"

Map to SDAF VM image configuration:
- "SUSE latest" / "SLES 15 SP5" → {{"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"}}
- "SUSE 15 SP4" / "SLES 15 SP4" → {{"publisher": "SUSE", "offer": "sles-sap-15-sp4", "sku": "gen2"}}
- "SUSE 12 SP5" / "SLES 12 SP5" → {{"publisher": "SUSE", "offer": "sles-sap-12-sp5", "sku": "gen2"}}
- "Red Hat latest" / "RHEL 9" → {{"publisher": "RedHat", "offer": "RHEL-SAP-HA", "sku": "9_0"}}
- "RHEL 8.6" / "Red Hat 8.6" → {{"publisher": "RedHat", "offer": "RHEL-SAP-HA", "sku": "8.6"}}
- "RHEL 8.4" → {{"publisher": "RedHat", "offer": "RHEL-SAP-HA", "sku": "8.4"}}

Return ONLY a valid JSON object with publisher, offer, and sku.
Default to SLES 15 SP5 if unclear.
"""

    try:
        response = await llm.ainvoke(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        # Default to SLES 15 SP5
        return {"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"}
    except Exception as e:
        logger.error(f"Failed to parse OS input: {e}")
        return {"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"}

# =============================================================================
# TFVARS GENERATION
# =============================================================================

def load_defaults() -> Dict[str, Any]:
    """Load default values from easy_defaults.yaml"""
    try:
        defaults_path = TEMPLATES_DIR / "easy_defaults.yaml"
        with open(defaults_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load defaults: {e}")
        return {}

def generate_tfvars(user_data: Dict[str, Any]) -> str:
    """Generate SDAF-compliant tfvars file from collected user data"""
    try:
        # Load defaults
        config = load_defaults()

        # Update with user-collected data
        # Prompt 0: Environment
        if "environment" in user_data:
            config["environment"] = user_data["environment"]
        if "location" in user_data:
            config["location"] = user_data["location"]
        if "network_logical_name" in user_data:
            config["network_logical_name"] = user_data["network_logical_name"]

        # Prompt 1: SAP System
        if "sid" in user_data:
            config["sid"] = user_data["sid"]
            config["sap_sid"] = user_data["sid"]
            config["sap_system_name"] = user_data["sid"]
        if "database_sid" in user_data:
            config["database_sid"] = user_data["database_sid"]
        if "database_platform" in user_data:
            config["database_platform"] = user_data["database_platform"]

        # Prompt 2: Sizing
        if "database_size" in user_data:
            config["database_size"] = user_data["database_size"]
        if "app_tier_sizing_dictionary_key" in user_data:
            config["app_tier_sizing_dictionary_key"] = user_data["app_tier_sizing_dictionary_key"]

        # Prompt 3: Architecture
        if "enable_app_tier_deployment" in user_data:
            config["enable_app_tier_deployment"] = user_data["enable_app_tier_deployment"]
        if "application_server_count" in user_data:
            config["application_server_count"] = user_data["application_server_count"]
        if "scs_server_count" in user_data:
            config["scs_server_count"] = user_data["scs_server_count"]
        if "database_server_count" in user_data:
            config["database_server_count"] = user_data["database_server_count"]
        if "database_high_availability" in user_data:
            config["database_high_availability"] = user_data["database_high_availability"]
        if "scs_high_availability" in user_data:
            config["scs_high_availability"] = user_data["scs_high_availability"]

        # Prompt 4: Network
        if user_data.get("network_type") == "greenfield":
            config["admin_subnet_address_prefix"] = user_data.get("admin_subnet", "10.1.0.0/24")
            config["db_subnet_address_prefix"] = user_data.get("db_subnet", "10.1.1.0/24")
            config["app_subnet_address_prefix"] = user_data.get("app_subnet", "10.1.2.0/24")
            config["web_subnet_address_prefix"] = user_data.get("web_subnet", "10.1.3.0/24")

        # Prompt 5: OS
        if "os_publisher" in user_data:
            vm_image = {
                "os_type": "LINUX",
                "publisher": user_data["os_publisher"],
                "offer": user_data["os_offer"],
                "sku": user_data["os_sku"],
                "version": "latest",
                "type": "marketplace"
            }
            config["database_vm_image"] = vm_image
            config["scs_server_image"] = vm_image
            config["application_server_image"] = vm_image
            config["webdispatcher_server_image"] = vm_image

        # Add metadata
        config["_generated_by"] = "SDAF Chat Agent v2"
        config["_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Render template
        template = jinja_env.get_template("sap.tfvars.j2")
        return template.render(config=config)

    except Exception as e:
        logger.error(f"Failed to generate tfvars: {e}")
        return f"# Error generating tfvars: {str(e)}"

# =============================================================================
# CONVERSATION HANDLER
# =============================================================================

async def process_user_message(session: ChatSession, user_message: str) -> str:
    """Process user message based on current prompt"""

    current_prompt = session.current_prompt

    # Prompt 0: Environment Identity
    if current_prompt == 0:
        parsed = await parse_environment_input(user_message)

        # Validate required fields
        if parsed.get("environment") and parsed.get("location") and parsed.get("network_logical_name"):
            session.user_data.update(parsed)
            session.current_prompt = 1

            # Return next prompt
            return get_prompt_message(1, session.user_data)
        else:
            return f"""I couldn't extract all three required values. Please provide:
1. Environment (DEV/PROD/QA)
2. Azure region (westeurope, eastus, etc)
3. Network name (max 7 chars)

Example: "DEV in westeurope, network SAP01"
"""

    # Prompt 1: SAP System Identity
    elif current_prompt == 1:
        parsed = await parse_sap_system_input(user_message)

        if parsed.get("sid") and parsed.get("database_sid") and parsed.get("database_platform"):
            session.user_data.update(parsed)
            session.current_prompt = 2

            return get_prompt_message(2, session.user_data)
        else:
            return """I couldn't extract the SAP system details. Please provide:
1. SAP Application SID (3 chars)
2. Database SID (3 chars)
3. Database platform (HANA/ORACLE/SQLSERVER/etc)

Example: "SID X00, database HDB, using HANA"
"""

    # Prompt 2: System Sizing
    elif current_prompt == 2:
        parsed = await parse_sizing_input(user_message)

        session.user_data["database_size"] = parsed.get("database_size", "Demo")
        session.user_data["app_tier_sizing_dictionary_key"] = parsed.get("app_tier_sizing", "Optimized")
        session.user_data["purpose"] = parsed.get("purpose", "development")
        session.user_data["size_description"] = parsed.get("database_size", "Demo")

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

        # Generate tfvars
        session.current_prompt = 6
        session.tfvars_content = generate_tfvars(session.user_data)
        session.tfvars_ready = True

        # Generate summary
        return generate_final_summary(session)

    else:
        return "Configuration is complete! You can download the tfvars file or start a new session."

def generate_final_summary(session: ChatSession) -> str:
    """Generate final configuration summary"""
    data = session.user_data

    # Build server counts
    db_count = data.get("database_server_count", 1)
    scs_count = data.get("scs_server_count", 1)
    app_count = data.get("application_server_count", 0)

    # HA statement
    ha_statement = ""
    if data.get("database_high_availability") or data.get("scs_high_availability"):
        ha_statement = " with High Availability enabled"

    summary = f"""Perfect! I have everything I need. Let me summarize your SAP deployment configuration:

**Environment:** {data.get('environment', '')} in {data.get('location', '')}
**Network:** {data.get('network_logical_name', '')}
**SAP System:** {data.get('sid', '')} ({data.get('database_platform', '')} database: {data.get('database_sid', '')})
**Sizing:** {data.get('size_description', '')} ({data.get('database_size', '')})
**Architecture:** {data.get('architecture_type', '')}{ha_statement}
**Servers:**
  - Database: {db_count} server(s)
  - SCS: {scs_count} server(s)
  - Application: {app_count} server(s)
**Network:** {data.get('network_type', 'greenfield').capitalize()} deployment
**Operating System:** {data.get('os_publisher', '')} {data.get('os_offer', '')}

✅ Your SDAF-compliant tfvars file has been generated!

You can now download the file using the download button, or ask me to explain any of these settings.
"""

    return summary

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
    return {"status": "ok", "version": "2.0.0"}

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

        return session.to_dict()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
