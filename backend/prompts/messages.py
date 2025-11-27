"""
Prompt Messages
===============

All conversation prompts and response generators for the 6-prompt flow.
Enhanced with numbered options and clear validation feedback.
"""

from typing import Dict, Any
from utils.helpers import get_region_code


def get_prompt_message(prompt_num: int, context: Dict[str, Any] = None) -> str:
    """Get the message for each of the 6 prompts"""
    context = context or {}

    if prompt_num == 0:
        # Prompt 0: Welcome + Environment Identity
        return """Hi! I'll help you create an SAP deployment configuration.

**Quick Start** - Type a number for a pre-configured template:
| # | Template | Description |
|---|----------|-------------|
| **1** | S/4HANA Development | DEV, HANA, small sizing |
| **2** | S/4HANA QA/Test | QA, HANA, medium sizing |
| **3** | S/4HANA Production | PROD, HANA, large sizing |
| **4** | Demo/Sandbox | SBX, minimal resources |

**Or provide your custom configuration:**

I need **3 things** to get started:

**[1] Environment** (required)
> DEV, QA, PROD, TEST, SBX, LAB, DEMO

**[2] Azure Region** (required)
> westeurope, northeurope, eastus, germanywestcentral, uksouth, ...

**[3] Network Name** (required, 3-7 characters)
> Example: SAP01, NET01, VNET1

**How to answer:**
- All at once: `DEV, westeurope, SAP01`
- One by one: `DEV` → then `westeurope` → then `SAP01`
- Natural: `Development environment in West Europe, network SAP01`
"""

    elif prompt_num == 1:
        # Prompt 1: SAP System Identity
        env = context.get("environment", "")
        location = context.get("location", "")
        network = context.get("network_logical_name", "")

        return f"""**Environment configured:** {env} in {location} (Network: {network})

Now I need your **SAP System Identity**:

**[1] SAP Application SID** (required, exactly 3 characters)
> Examples: X00, D01, P01, S4H
> Rules: Letters + numbers, must start with a letter

**[2] Database SID** (required, exactly 3 characters)
> Usually: HDB (for HANA), XDB, ORA
> Rules: Same as SID - letters + numbers, starts with letter

**[3] Database Platform** (required)
| # | Platform | Description |
|---|----------|-------------|
| **1** | HANA | SAP HANA (recommended for S/4HANA) |
| **2** | DB2 | IBM DB2 |
| **3** | ORACLE | Oracle Database |
| **4** | ASE | SAP ASE (Sybase) |
| **5** | SQLSERVER | Microsoft SQL Server |
| **6** | NONE | No database tier |

**How to answer:**
- All at once: `X00, HDB, HANA` or `X00, HDB, 1`
- One by one: `X00` → then `HDB` → then `HANA`
- Natural: `SID is X00, database HDB, using HANA`
"""

    elif prompt_num == 2:
        # Prompt 2: System Sizing
        sid = context.get("sid", "")
        platform = context.get("database_platform", "")
        db_sid = context.get("database_sid", "")

        return f"""**SAP System configured:** {sid} with {platform} database ({db_sid})

Now let's determine the **sizing**:

**[1] Purpose** - What is this system for?
| # | Purpose | Recommendation |
|---|---------|----------------|
| **1** | Demo/Testing | Minimal resources |
| **2** | Development | Small sizing |
| **3** | QA/Staging | Medium sizing |
| **4** | Production | Large sizing |
| **5** | High-Load Production | Extra-large sizing |

**[2] Database Size** - How much memory?
| # | Size | Memory | VM SKU |
|---|------|--------|--------|
| **1** | Demo | 32 GB | D8s_v3 |
| **2** | Small | 160 GB | E20ds_v4 |
| **3** | Medium | 256 GB | E32ds_v4 |
| **4** | Large | 512 GB | E64ds_v5 |
| **5** | XLarge | 1-2 TB | M128s |
| **6** | XXLarge | 4+ TB | M208ms_v2 |

**How to answer:**
- Simple: `demo` or `1` or `small`
- Descriptive: `Development, small sizing`
- Memory-based: `I need about 256GB`
"""

    elif prompt_num == 3:
        # Prompt 3: Architecture Pattern
        purpose = context.get("purpose", "workload")
        size_desc = context.get("size_description", "")

        return f"""**Sizing configured:** {purpose} workload with {size_desc} sizing

Now choose your **architecture**:

**[1] Deployment Type**
| # | Type | Description |
|---|------|-------------|
| **1** | Standalone | All components on one server (simplest, for dev/test) |
| **2** | Distributed | Separate DB + SCS + App servers (recommended for production) |

**[2] High Availability** (only for Distributed)
| # | Option | Description |
|---|--------|-------------|
| **1** | No HA | Single instance, cost-optimized |
| **2** | With HA | Clustered, zero-downtime (requires 2+ servers) |

**[3] Application Servers** (only for Distributed)
> How many app servers? Typically 1-4 for most systems

**How to answer:**
- Simple: `standalone` or `1`
- Detailed: `Distributed with 2 app servers, no HA`
- For dev/test: Just say `standalone, no HA`
"""

    elif prompt_num == 4:
        # Prompt 4: Network Configuration
        arch_type = context.get("architecture_type", "deployment")
        ha_statement = " with HA" if context.get("ha_enabled") else ""

        return f"""**Architecture configured:** {arch_type}{ha_statement}

Now for the **network setup**:

**Network Type**
| # | Type | Description |
|---|------|-------------|
| **1** | Greenfield | SDAF creates a new VNet with subnets (recommended) |
| **2** | Brownfield | Use existing VNet/subnets (requires ARM IDs) |

**If Greenfield** - Default subnets (you can customize):
| Subnet | Default CIDR |
|--------|--------------|
| Admin | 10.1.0.0/24 |
| Database | 10.1.1.0/24 |
| Application | 10.1.2.0/24 |
| Web | 10.1.3.0/24 |

**How to answer:**
- Accept defaults: `greenfield` or `1` or `defaults are fine`
- Custom CIDRs: `greenfield, use 10.10.x.x range`
- Brownfield: `brownfield` (I'll ask for subnet IDs)
"""

    elif prompt_num == 5:
        # Prompt 5: Operating System
        return """Almost done! Choose your **Operating System**:

**SUSE Linux Enterprise Server (recommended)**
| # | Version | Notes |
|---|---------|-------|
| **1** | SLES 15 SP5 | Latest, recommended |
| **2** | SLES 15 SP4 | Previous stable |
| **3** | SLES 15 SP3 | Older stable |
| **4** | SLES 12 SP5 | Legacy support |

**Red Hat Enterprise Linux**
| # | Version | Notes |
|---|---------|-------|
| **5** | RHEL 9.x | Latest |
| **6** | RHEL 8.6 | Stable |
| **7** | RHEL 8.4 | Older stable |

**How to answer:**
- Simple: `SUSE` or `1` or `SLES 15 SP5`
- Short: `Red Hat 8` or `RHEL 9`
- Full: `sles-sap-15-sp5`
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
    return """Hey! I'm your **SAP Deployment Assistant** and I'll help you create a tfvars file for the **SAP Deployment Automation Framework (SDAF)**.

**Quick Start Options:**

| # | Template | Description |
|---|----------|-------------|
| **1** | S/4HANA Development | DEV, HANA, single instance |
| **2** | S/4HANA QA/Test | QA, HANA, medium sizing |
| **3** | S/4HANA Production | PROD, HANA, large sizing |
| **4** | Demo/Sandbox | Minimal resources |

Just type a **number** (1-4) for quick setup, or tell me your custom configuration:
- **Environment** (DEV/PROD/QA)
- **Azure Region** (westeurope, eastus, ...)
- **Network Name** (SAP01, NET01, ...)

Example: `DEV in westeurope, network SAP01`
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


def generate_missing_fields_message(missing: list, collected: dict) -> str:
    """Generate a helpful message about missing fields"""
    msg = ""

    if collected:
        collected_list = ", ".join([f"**{k}**: {v}" for k, v in collected.items()])
        msg += f"Got it! {collected_list}\n\n"

    if missing:
        msg += "I still need:\n"
        for i, field in enumerate(missing, 1):
            msg += f"{i}. {field}\n"
        msg += "\nYou can provide one value at a time or all at once."

    return msg


def generate_validation_error(field: str, value: str, error: str, suggestions: list = None) -> str:
    """Generate a helpful validation error message"""
    msg = f"""**Invalid {field}:** `{value}`

**Error:** {error}
"""
    if suggestions:
        msg += f"\n**Did you mean?** {', '.join(suggestions[:5])}"

    return msg


def generate_confirmation_summary(user_data: Dict[str, Any]) -> str:
    """Generate summary for user confirmation BEFORE generating tfvars"""

    # Build server counts
    db_count = user_data.get("database_server_count", 1)
    scs_count = user_data.get("scs_server_count", 0)
    app_count = user_data.get("application_server_count", 0)

    # HA indicators
    ha_db = "Yes" if user_data.get("database_high_availability") else "No"
    ha_scs = "Yes" if user_data.get("scs_high_availability") else "No"

    # Generate filename preview
    filename = generate_sdaf_filename(user_data)

    summary = f"""## Please Review Your Configuration

| Category | Parameter | Value |
|----------|-----------|-------|
| **Environment** | Environment | {user_data.get('environment', 'N/A')} |
| | Azure Region | {user_data.get('location', 'N/A')} |
| | Network Name | {user_data.get('network_logical_name', 'N/A')} |
| **SAP System** | Application SID | {user_data.get('sid', 'N/A')} |
| | Database SID | {user_data.get('database_sid', 'N/A')} |
| | Database Platform | {user_data.get('database_platform', 'N/A')} |
| | Database Size | {user_data.get('database_size', 'N/A')} |
| **Architecture** | Type | {user_data.get('architecture_type', 'standalone').capitalize()} |
| | DB Servers | {db_count} (HA: {ha_db}) |
| | SCS Servers | {scs_count} (HA: {ha_scs}) |
| | App Servers | {app_count} |
| **Network** | Type | {user_data.get('network_type', 'greenfield').capitalize()} |
| **OS** | Operating System | {user_data.get('os_publisher', 'SUSE')} {user_data.get('os_offer', 'sles-sap-15-sp5')} |

**Filename:** `{filename}`

---

**Is everything correct?**
- Type **yes** or **confirm** to generate the file
- Type **no** or **change** to modify values
"""

    return summary


def generate_final_summary(user_data: Dict[str, Any]) -> str:
    """Generate clean configuration summary after confirmation"""

    # Build server counts
    db_count = user_data.get("database_server_count", 1)
    scs_count = user_data.get("scs_server_count", 0)
    app_count = user_data.get("application_server_count", 0)

    # HA indicator
    ha_db = "Yes" if user_data.get("database_high_availability") else "No"
    ha_scs = "Yes" if user_data.get("scs_high_availability") else "No"

    # Generate SDAF filename
    filename = generate_sdaf_filename(user_data)

    summary = f"""## Configuration Complete!

| Category | Parameter | Value |
|----------|-----------|-------|
| **Environment** | Environment | {user_data.get('environment', 'N/A')} |
| | Azure Region | {user_data.get('location', 'N/A')} |
| | Network Name | {user_data.get('network_logical_name', 'N/A')} |
| **SAP System** | Application SID | {user_data.get('sid', 'N/A')} |
| | Database SID | {user_data.get('database_sid', 'N/A')} |
| | Database Platform | {user_data.get('database_platform', 'N/A')} |
| | Database Size | {user_data.get('database_size', 'N/A')} |
| **Architecture** | Type | {user_data.get('architecture_type', 'standalone').capitalize()} |
| | DB Servers | {db_count} (HA: {ha_db}) |
| | SCS Servers | {scs_count} (HA: {ha_scs}) |
| | App Servers | {app_count} |
| **Network** | Type | {user_data.get('network_type', 'greenfield').capitalize()} |
| **OS** | Operating System | {user_data.get('os_publisher', 'SUSE')} {user_data.get('os_offer', 'sles-sap-15-sp5')} |

---

### Download Ready

Your **SDAF-compliant tfvars file** is ready: `{filename}`

Click the **Download** button to get your configuration file.

_This file contains all required SDAF parameters with best-practice defaults._
"""

    return summary
