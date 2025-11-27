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
import asyncio
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

# LLM Timeout Configuration
LLM_TIMEOUT_SECONDS = 15  # Max time to wait for LLM response

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
            SELECT s.session_id, s.title, s.current_prompt, s.tfvars_ready, s.created_at, s.updated_at,
                   COUNT(m.id) as message_count
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
        """)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "title": row[1],
                "current_prompt": row[2],
                "tfvars_ready": bool(row[3]),
                "created_at": row[4],
                "updated_at": row[5],
                "message_count": row[6]
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
# REGEX FALLBACK FUNCTIONS - Fast parsing for simple patterns
# =============================================================================

def normalize_azure_region(region: str) -> str:
    """Normalize Azure region names to canonical form"""
    region_map = {
        "west europe": "westeurope",
        "west-europe": "westeurope",
        "east us": "eastus",
        "east-us": "eastus",
        "north europe": "northeurope",
        "north-europe": "northeurope",
        "germany west central": "germanywestcentral",
        "germany-west-central": "germanywestcentral"
    }
    region_lower = region.lower().strip()
    return region_map.get(region_lower, region_lower.replace(" ", "").replace("-", ""))

def get_region_code(region: str) -> str:
    """Convert Azure region to SDAF 4-letter code"""
    region_codes = {
        "westeurope": "WEEU",
        "northeurope": "NOEU",
        "eastus": "EAUS",
        "eastus2": "EUS2",
        "westus": "WEUS",
        "westus2": "WUS2",
        "centralus": "CEUS",
        "southcentralus": "SCUS",
        "germanywestcentral": "GWCE",
        "uksouth": "UKSO",
        "ukwest": "UKWE",
        "francecentral": "FRCE",
        "switzerlandnorth": "SWNO",
        "norwayeast": "NOEA",
        "swedencentral": "SWCE"
    }
    region_normalized = normalize_azure_region(region)
    return region_codes.get(region_normalized, region_normalized[:4].upper())

def generate_sdaf_filename(user_data: Dict[str, Any]) -> str:
    """Generate SDAF-compliant filename: ENV-LOCATION-NETWORK-SID.tfvars

    Examples:
    - PRD-WEEU-SAP01-X00.tfvars
    - DEV-NOEU-SAP02-P01.tfvars
    """
    env = user_data.get("environment", "DEV").upper()[:5]
    location = user_data.get("location", "westeurope")
    region_code = get_region_code(location)  # WEEU, NOEU, etc.
    network = user_data.get("network_logical_name", "SAP01").upper()[:7]
    sid = user_data.get("sid", "X00").upper()

    return f"{env}-{region_code}-{network}-{sid}.tfvars"

VALID_AZURE_REGIONS = [
    "westeurope", "northeurope", "eastus", "eastus2", "westus", "westus2", "westus3",
    "centralus", "southcentralus", "northcentralus", "eastasia", "southeastasia",
    "japaneast", "japanwest", "australiaeast", "australiasoutheast", "brazilsouth",
    "canadacentral", "canadaeast", "uksouth", "ukwest", "francecentral", "francesouth",
    "germanywestcentral", "switzerlandnorth", "norwayeast", "swedencentral",
    "southafricanorth", "uaenorth", "koreacentral", "koreasouth", "centralindia",
    "southindia", "westindia", "qatarcentral", "polandcentral", "italynorth"
]

def validate_azure_region(region: str) -> Optional[str]:
    """Validate and normalize Azure region"""
    normalized = normalize_azure_region(region)
    if normalized.lower() in VALID_AZURE_REGIONS:
        return normalized.lower()
    return None

VALID_ENVIRONMENTS = ["DEV", "PROD", "PRD", "QA", "UAT", "TST", "TEST", "NONPROD", "NP", "SANDBOX", "SBX"]

def try_regex_parse_environment(msg: str, existing_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Fast regex parsing for environment input with partial support and context awareness"""

    existing_data = existing_data or {}
    has_env = existing_data.get("environment")
    has_location = existing_data.get("location")
    has_network = existing_data.get("network_logical_name")

    # FULL PATTERNS - All 3 values

    # Pattern 1: "DEV, westeurope, SAP01"
    pattern1 = r'^\s*(\w+)\s*[,/]\s*([\w\s-]+?)\s*[,/]\s*(\w+)\s*$'
    match = re.search(pattern1, msg, re.IGNORECASE)
    if match:
        region = validate_azure_region(match.group(2))
        if region:
            logger.info("✅ Regex: comma/slash - all 3")
            return {
                "environment": match.group(1).upper()[:5],
                "location": region,
                "network_logical_name": match.group(3).upper()[:7]
            }

    # Pattern 2: "DEV westeurope SAP01"
    pattern2 = r'^\s*(\w+)\s+([\w\s-]+?)\s+(\w+)\s*$'
    match = re.search(pattern2, msg, re.IGNORECASE)
    if match:
        region = validate_azure_region(match.group(2))
        if region:
            logger.info("✅ Regex: space - all 3")
            return {
                "environment": match.group(1).upper()[:5],
                "location": region,
                "network_logical_name": match.group(3).upper()[:7]
            }

    # Pattern 3: "dev in westeurope SAP01"
    pattern3 = r'(\w+)\s+in\s+([\w\s-]+?)(?:\s+(?:network\s*:?\s*)?(\w+))?$'
    match = re.search(pattern3, msg, re.IGNORECASE)
    if match and match.group(3):
        region = validate_azure_region(match.group(2).strip())
        if region:
            logger.info("✅ Regex: 'in' keyword - all 3")
            return {
                "environment": match.group(1).upper()[:5],
                "location": region,
                "network_logical_name": match.group(3).upper()[:7]
            }

    # PARTIAL PATTERNS - Support progressive input (CONTEXT-AWARE)

    # Pattern 4: Single word - could be ENV, REGION, or NETWORK depending on context
    pattern_single = r'^\s*(\w+)\s*$'
    match = re.search(pattern_single, msg, re.IGNORECASE)
    if match:
        word = match.group(1).upper()

        # Try as environment first (if not set)
        if not has_env and word in VALID_ENVIRONMENTS:
            logger.info(f"✅ Regex: Environment only = {word}")
            return {"environment": word[:5]}

        # Try as region (if env is set but location isn't)
        if has_env and not has_location:
            region = validate_azure_region(msg)
            if region:
                logger.info(f"✅ Regex: Region only = {region}")
                return {"location": region}

        # Otherwise treat as network name (if env and location are set)
        if has_env and has_location and not has_network:
            logger.info(f"✅ Regex: Network name only = {word}")
            return {"network_logical_name": word[:7]}

    # Pattern 5: Two words - could be "ENV REGION" or "REGION NETWORK"
    pattern_two = r'^\s*(\S+)\s+(\S+)\s*$'
    match = re.search(pattern_two, msg, re.IGNORECASE)
    if match:
        word1 = match.group(1).upper()
        word2 = match.group(2)

        # Try "ENV REGION"
        if not has_env and word1 in VALID_ENVIRONMENTS:
            region = validate_azure_region(word2)
            if region:
                logger.info("✅ Regex: Env + Region")
                return {
                    "environment": word1[:5],
                    "location": region
                }

        # Try "REGION NETWORK" (if env already set)
        if has_env and not has_location:
            region = validate_azure_region(word1)
            if region:
                logger.info("✅ Regex: Region + Network")
                return {
                    "location": region,
                    "network_logical_name": word2.upper()[:7]
                }

    logger.info("ℹ️ No regex pattern matched")
    return None

def try_regex_parse_sap_system(msg: str, existing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Context-aware parsing - doesn't overwrite already set values"""

    has_sid = existing_data.get("sid")
    has_db_sid = existing_data.get("database_sid")
    has_platform = existing_data.get("database_platform")

    # Pattern 1: "X00 HDB HANA" (all 3 values)
    pattern1 = r'^\s*([A-Z0-9]{3})\s+([A-Z0-9]{3})\s+(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)\s*$'
    match = re.search(pattern1, msg, re.IGNORECASE)
    if match:
        logger.info("✅ Regex: 3 values space-separated")
        return {
            "sid": match.group(1).upper(),
            "database_sid": match.group(2).upper(),
            "database_platform": match.group(3).upper()
        }

    # Pattern 2: "X00, HDB, HANA" (comma-separated)
    pattern2 = r'^\s*([A-Z0-9]{3})\s*,\s*([A-Z0-9]{3})\s*,\s*(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)\s*$'
    match = re.search(pattern2, msg, re.IGNORECASE)
    if match:
        logger.info("✅ Regex: 3 values comma-separated")
        return {
            "sid": match.group(1).upper(),
            "database_sid": match.group(2).upper(),
            "database_platform": match.group(3).upper()
        }

    # Pattern 3: "SID X00, DB HDB, platform HANA" (labeled)
    pattern3 = r'(?:sid\s*:?\s*)?([A-Z0-9]{3}).*?(?:db|database).*?([A-Z0-9]{3}).*?(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)'
    match = re.search(pattern3, msg, re.IGNORECASE)
    if match:
        logger.info("✅ Regex: labeled format")
        return {
            "sid": match.group(1).upper(),
            "database_sid": match.group(2).upper(),
            "database_platform": match.group(3).upper()
        }

    # PARTIAL: Two 3-char codes "X00 HDB" or "X00, HDB"
    pattern_two = r'^\s*([A-Z0-9]{3})\s*[,\s]+\s*([A-Z0-9]{3})\s*$'
    match = re.search(pattern_two, msg, re.IGNORECASE)
    if match:
        code1 = match.group(1).upper()
        code2 = match.group(2).upper()

        if not has_sid and not has_db_sid:
            # Neither set → assume SID + DB_SID
            logger.info("✅ Regex: SID + DB_SID")
            return {"sid": code1, "database_sid": code2}
        elif has_sid and not has_db_sid:
            # SID already set → both are DB_SID (second overwrites first)
            logger.info("✅ Regex: DB_SID update")
            return {"database_sid": code2}

    # PARTIAL: Single 3-char code "X00" or "HDB"
    pattern_single = r'^\s*([A-Z0-9]{3})\s*$'
    match = re.search(pattern_single, msg, re.IGNORECASE)
    if match:
        code = match.group(1).upper()

        # Context-aware: fill first missing slot
        if not has_sid:
            logger.info(f"✅ Regex: Setting SID = {code}")
            return {"sid": code}
        elif not has_db_sid:
            logger.info(f"✅ Regex: Setting DB_SID = {code}")
            return {"database_sid": code}
        else:
            # Both already set, ignore
            logger.info(f"⚠️ SID and DB_SID already set, ignoring '{code}'")
            return {}

    # PARTIAL: Platform only "HANA" or "ORACLE"
    pattern_platform = r'^\s*(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)\s*$'
    match = re.search(pattern_platform, msg, re.IGNORECASE)
    if match:
        if not has_platform:
            logger.info("✅ Regex: Platform only")
            return {"database_platform": match.group(1).upper()}
        else:
            logger.info(f"⚠️ Platform already set, ignoring")
            return {}

    return None

# =============================================================================
# LLM PARSING FUNCTIONS - Natural Language Understanding with Timeout
# =============================================================================

async def parse_environment_input(user_message: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Parse environment input using Hybrid approach (Regex → LLM with timeout)"""

    existing_data = existing_data or {}

    # STAGE 1: Try fast regex parsing first (with context)
    regex_result = try_regex_parse_environment(user_message, existing_data)
    if regex_result:
        return regex_result

    # STAGE 2: Use LLM with timeout for complex input
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
        logger.info(f"⏱️ Using LLM for complex environment input (timeout: {LLM_TIMEOUT_SECONDS}s)")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout after {LLM_TIMEOUT_SECONDS}s for input: {user_message}")
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to parse environment input: {e}")
        return {}

async def parse_sap_system_input(user_message: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse SAP system identity using Hybrid approach (Regex → LLM with timeout)"""

    # STAGE 1: Try fast regex parsing first (context-aware)
    regex_result = try_regex_parse_sap_system(user_message, existing_data)
    if regex_result:
        return regex_result

    # STAGE 2: Use LLM with timeout
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
        logger.info(f"⏱️ Using LLM for SAP system input (timeout: {LLM_TIMEOUT_SECONDS}s)")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout after {LLM_TIMEOUT_SECONDS}s")
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to parse SAP system input: {e}")
        return {}

async def parse_sizing_input(user_message: str) -> Dict[str, Any]:
    """Parse sizing requirements from user input with timeout"""
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
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout, using defaults for sizing")
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}
    except Exception as e:
        logger.error(f"❌ Failed to parse sizing input: {e}")
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}

async def parse_architecture_input(user_message: str) -> Dict[str, Any]:
    """Parse architecture pattern from user input with timeout"""
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
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout, using standalone defaults")
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}
    except Exception as e:
        logger.error(f"❌ Failed to parse architecture input: {e}")
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}

async def parse_network_input(user_message: str) -> Dict[str, Any]:
    """Parse network configuration from user input with timeout"""
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
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"network_type": "greenfield", "custom_cidrs": False}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout, using greenfield defaults")
        return {"network_type": "greenfield", "custom_cidrs": False}
    except Exception as e:
        logger.error(f"❌ Failed to parse network input: {e}")
        return {"network_type": "greenfield", "custom_cidrs": False}

async def parse_os_input(user_message: str) -> Dict[str, Any]:
    """Parse operating system selection from user input with timeout"""
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
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        # Default to SLES 15 SP5
        return {"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout, using SLES 15 SP5 default")
        return {"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"}
    except Exception as e:
        logger.error(f"❌ Failed to parse OS input: {e}")
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
# INTENT DETECTION
# =============================================================================

def is_greeting(message: str) -> bool:
    """Detect if message is a greeting"""
    greetings = ["hallo", "hi", "hey", "hello", "guten tag", "moin", "servus", "grüß gott"]
    msg_lower = message.lower().strip()
    return any(greeting in msg_lower for greeting in greetings)

def get_greeting_response() -> str:
    """Return friendly greeting response"""
    return """Hey! 👋 Schön dich kennenzulernen!

Ich bin dein **SAP Deployment Assistant** und helfe dir dabei, eine tfvars-Datei für das **SAP Deployment Automation Framework (SDAF)** zu erstellen.

Mit dieser Datei kannst du dann dein SAP System automatisiert auf Azure deployen - ganz ohne manuelles Terraform-Gefummel! 🚀

**Wie läuft's ab?**
Ich stelle dir ein paar kurze Fragen zu deinem geplanten SAP System:
- Welche Umgebung? (DEV, PROD, QA, ...)
- In welcher Azure Region?
- Welche SAP SID?
- Welche Größe brauchst du?
- ... und ein paar Details mehr

Am Ende bekommst du eine **SDAF-konforme tfvars-Datei** zum Download, die du direkt verwenden kannst!

**Bereit loszulegen?** 💪
Dann sag mir: In welcher **Umgebung** (DEV/PROD/QA), **Azure Region** und mit welchem **Netzwerknamen** (max 7 Zeichen) möchtest du deployen?

Beispiel: "DEV in westeurope, network SAP01"
"""

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
            missing.append("**Environment** (DEV/PROD/QA)")
        if not has_location:
            missing.append("**Azure region** (westeurope, eastus, etc)")
        if not has_network:
            missing.append("**Network name** (max 7 chars)")

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
            missing.append("**SAP Application SID** (3 chars, like X00, P01)")
        if not has_db_sid:
            missing.append("**Database SID** (3 chars, like HDB, XDB, ORA)")
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
        return generate_confirmation_summary(session)

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

def generate_confirmation_summary(session: ChatSession) -> str:
    """Generate summary for user confirmation BEFORE generating tfvars"""
    data = session.user_data

    # Build server counts
    db_count = data.get("database_server_count", 1)
    scs_count = data.get("scs_server_count", 1)
    app_count = data.get("application_server_count", 0)

    # HA indicators
    ha_db = "✓ Ja" if data.get("database_high_availability") else "✗ Nein"
    ha_scs = "✓ Ja" if data.get("scs_high_availability") else "✗ Nein"

    # Generate filename preview
    filename = generate_sdaf_filename(data)

    summary = f"""## 📋 Bitte überprüfe deine Konfiguration

Ich habe alle Informationen gesammelt. Hier ist die Zusammenfassung:

### 🌍 Umgebung
| Parameter | Wert |
|-----------|------|
| **Environment** | {data.get('environment', 'N/A')} |
| **Azure Region** | {data.get('location', 'N/A')} |
| **Netzwerkname** | {data.get('network_logical_name', 'N/A')} |

### 💾 SAP System
| Parameter | Wert |
|-----------|------|
| **Application SID** | {data.get('sid', 'N/A')} |
| **Database SID** | {data.get('database_sid', 'N/A')} |
| **Database Platform** | {data.get('database_platform', 'N/A')} |
| **Database Size** | {data.get('database_size', 'N/A')} |

### 🏗️ Architektur
| Komponente | Anzahl | High Availability |
|------------|--------|-------------------|
| **Database Server** | {db_count} | {ha_db} |
| **Central Services** | {scs_count} | {ha_scs} |
| **Application Server** | {app_count} | - |
| **Typ** | {data.get('architecture_type', 'standalone').capitalize()} | - |

### 🌐 Netzwerk & OS
| Parameter | Wert |
|-----------|------|
| **Netzwerk-Typ** | {data.get('network_type', 'greenfield').capitalize()} |
| **Betriebssystem** | {data.get('os_publisher', 'SUSE')} {data.get('os_offer', 'sles-sap-15-sp5')} |

### 📁 Dateiname
Die generierte Datei wird heißen: **`{filename}`**

---

## ✅ Ist alles korrekt?

Antworte mit:
- **"Ja"** oder **"Bestätigen"** → Download wird freigegeben
- **"Nein"** oder **"Ändern"** → Du kannst Werte korrigieren

Was sagst du? 🤔
"""

    return summary

def generate_final_summary(session: ChatSession) -> str:
    """Generate clean, table-formatted configuration summary"""
    data = session.user_data

    # Build server counts
    db_count = data.get("database_server_count", 1)
    scs_count = data.get("scs_server_count", 1)
    app_count = data.get("application_server_count", 0)

    # HA indicator
    ha_db = "✓" if data.get("database_high_availability") else "✗"
    ha_scs = "✓" if data.get("scs_high_availability") else "✗"

    # Generate SDAF filename
    filename = generate_sdaf_filename(data)

    summary = f"""## ✅ Configuration Complete!

Here's your SAP deployment summary:

### 📋 Basic Information
| Parameter | Value |
|-----------|-------|
| **Environment** | {data.get('environment', 'N/A')} |
| **Azure Region** | {data.get('location', 'N/A')} |
| **Network Name** | {data.get('network_logical_name', 'N/A')} |

### 🖥️ SAP System
| Parameter | Value |
|-----------|-------|
| **Application SID** | {data.get('sid', 'N/A')} |
| **Database SID** | {data.get('database_sid', 'N/A')} |
| **Database Platform** | {data.get('database_platform', 'N/A')} |
| **Database Size** | {data.get('database_size', 'N/A')} |

### 🏗️ Architecture
| Component | Count | High Availability |
|-----------|-------|-------------------|
| **Database Servers** | {db_count} | {ha_db} |
| **Central Services (SCS)** | {scs_count} | {ha_scs} |
| **Application Servers** | {app_count} | - |
| **Deployment Type** | {data.get('architecture_type', 'standalone').capitalize()} | - |

### 🌐 Network & OS
| Parameter | Value |
|-----------|-------|
| **Network Type** | {data.get('network_type', 'greenfield').capitalize()} |
| **Operating System** | {data.get('os_publisher', 'SUSE')} {data.get('os_offer', 'sles-sap-15-sp5')} |

---

### 📥 Download
Your **SDAF-compliant tfvars file** is ready: `{filename}`

Use the download button below to get your configuration file!

💡 *This file contains 180+ pre-configured SDAF parameters with best-practice defaults.*
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
