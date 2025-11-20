"""
Prompt Messages
===============

All conversation prompts and response generators for the 6-prompt flow.
"""

from typing import Dict, Any
from utils.helpers import get_region_code


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


def generate_confirmation_summary(user_data: Dict[str, Any]) -> str:
    """Generate summary for user confirmation BEFORE generating tfvars"""

    # Build server counts
    db_count = user_data.get("database_server_count", 1)
    scs_count = user_data.get("scs_server_count", 1)
    app_count = user_data.get("application_server_count", 0)

    # HA indicators
    ha_db = "✓ Ja" if user_data.get("database_high_availability") else "✗ Nein"
    ha_scs = "✓ Ja" if user_data.get("scs_high_availability") else "✗ Nein"

    # Generate filename preview
    filename = generate_sdaf_filename(user_data)

    summary = f"""## 📋 Bitte überprüfe deine Konfiguration

Ich habe alle Informationen gesammelt. Hier ist die Zusammenfassung:

### 🌍 Umgebung
| Parameter | Wert |
|-----------|------|
| **Environment** | {user_data.get('environment', 'N/A')} |
| **Azure Region** | {user_data.get('location', 'N/A')} |
| **Netzwerkname** | {user_data.get('network_logical_name', 'N/A')} |

### 💾 SAP System
| Parameter | Wert |
|-----------|------|
| **Application SID** | {user_data.get('sid', 'N/A')} |
| **Database SID** | {user_data.get('database_sid', 'N/A')} |
| **Database Platform** | {user_data.get('database_platform', 'N/A')} |
| **Database Size** | {user_data.get('database_size', 'N/A')} |

### 🏗️ Architektur
| Komponente | Anzahl | High Availability |
|------------|--------|-------------------|
| **Database Server** | {db_count} | {ha_db} |
| **Central Services** | {scs_count} | {ha_scs} |
| **Application Server** | {app_count} | - |
| **Typ** | {user_data.get('architecture_type', 'standalone').capitalize()} | - |

### 🌐 Netzwerk & OS
| Parameter | Wert |
|-----------|------|
| **Netzwerk-Typ** | {user_data.get('network_type', 'greenfield').capitalize()} |
| **Betriebssystem** | {user_data.get('os_publisher', 'SUSE')} {user_data.get('os_offer', 'sles-sap-15-sp5')} |

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


def generate_final_summary(user_data: Dict[str, Any]) -> str:
    """Generate clean, table-formatted configuration summary"""

    # Build server counts
    db_count = user_data.get("database_server_count", 1)
    scs_count = user_data.get("scs_server_count", 1)
    app_count = user_data.get("application_server_count", 0)

    # HA indicator
    ha_db = "✓" if user_data.get("database_high_availability") else "✗"
    ha_scs = "✓" if user_data.get("scs_high_availability") else "✗"

    # Generate SDAF filename
    filename = generate_sdaf_filename(user_data)

    summary = f"""## ✅ Configuration Complete!

Here's your SAP deployment summary:

### 📋 Basic Information
| Parameter | Value |
|-----------|-------|
| **Environment** | {user_data.get('environment', 'N/A')} |
| **Azure Region** | {user_data.get('location', 'N/A')} |
| **Network Name** | {user_data.get('network_logical_name', 'N/A')} |

### 🖥️ SAP System
| Parameter | Value |
|-----------|-------|
| **Application SID** | {user_data.get('sid', 'N/A')} |
| **Database SID** | {user_data.get('database_sid', 'N/A')} |
| **Database Platform** | {user_data.get('database_platform', 'N/A')} |
| **Database Size** | {user_data.get('database_size', 'N/A')} |

### 🏗️ Architecture
| Component | Count | High Availability |
|-----------|-------|-------------------|
| **Database Servers** | {db_count} | {ha_db} |
| **Central Services (SCS)** | {scs_count} | {ha_scs} |
| **Application Servers** | {app_count} | - |
| **Deployment Type** | {user_data.get('architecture_type', 'standalone').capitalize()} | - |

### 🌐 Network & OS
| Parameter | Value |
|-----------|-------|
| **Network Type** | {user_data.get('network_type', 'greenfield').capitalize()} |
| **Operating System** | {user_data.get('os_publisher', 'SUSE')} {user_data.get('os_offer', 'sles-sap-15-sp5')} |

---

### 📥 Download
Your **SDAF-compliant tfvars file** is ready: `{filename}`

Use the download button below to get your configuration file!

💡 *This file contains 180+ pre-configured SDAF parameters with best-practice defaults.*
"""

    return summary
