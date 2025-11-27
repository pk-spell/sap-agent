"""
SAP Deployment Agent V3 - Hybrid Approach
==========================================

Uses V2's proven conversation logic with V3's LLM-Factory.

Key Changes from V2:
- LLM is now configurable (via config.yaml)
- Quick-select templates (1-4) for common configurations
- Regex-first parsing with typo correction via normalizer
- Numbered options for all prompts

This ensures:
- Same prompts as V2 (grouped questions, clear examples)
- Same data structure (flat user_data)
- Same error handling
- But with swappable LLMs!
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# LLM Factory
from config_loader import get_config

# V2's proven parsers (with normalizer integration)
from parsers import (
    parse_environment_input,
    parse_sap_system_input,
    parse_sizing_input,
    parse_architecture_input,
    parse_network_input,
    parse_os_input
)

# V2's prompts (ORIGINAL!)
from prompts import (
    get_prompt_message,
    is_greeting,
    get_greeting_response,
    generate_confirmation_summary,
    generate_final_summary,
    generate_sdaf_filename
)

# Quick templates
from config_data.quick_templates import find_template_by_input, get_template_summary

# TFVARS Generator
from tfvars import generate_tfvars

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Agent State - Compatible with V2's ChatSession"""
    current_prompt: int = 0
    user_data: Dict[str, Any] = field(default_factory=dict)
    messages: list = field(default_factory=list)  # List[Tuple[str, str]]
    tfvars_ready: bool = False
    tfvars_content: str = ""

    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.messages.append((role, content))


class SAPAgentV3:
    """SAP Agent V3 - V2 Logic + V3 LLM-Factory"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize with configurable LLM"""
        self.config = get_config(config_path)

        # Get LLMs from config
        self.parsing_llm = self.config.get_llm("parsing")
        self.default_llm = self.config.get_llm("default")

        # Agent state
        self.state = AgentState()

    async def get_welcome_message(self) -> str:
        """Get initial welcome message"""
        return get_prompt_message(0)

    async def process_message(self, user_input: str) -> str:
        """
        Process user message - IDENTICAL TO V2's process_user_message()

        Args:
            user_input: User's message

        Returns:
            Agent's response
        """
        # Add user message to history
        self.state.add_message("user", user_input)

        # GREETING DETECTION - respond friendly regardless of current prompt
        if is_greeting(user_input):
            response = get_greeting_response()
            self.state.add_message("assistant", response)
            return response

        current_prompt = self.state.current_prompt

        # Prompt 0: Environment Identity - Progressive Questioning
        if current_prompt == 0:
            # CHECK FOR QUICK TEMPLATE SELECTION FIRST (1-4)
            template = find_template_by_input(user_input)
            if template:
                # Apply template config to user_data
                self.state.user_data.update(template["config"])

                # Jump to confirmation (prompt 6) since template provides everything
                self.state.current_prompt = 6

                # Generate summary showing selected template
                summary = get_template_summary(template)
                response = f"""**Template Selected!**

{summary}

{generate_confirmation_summary(self.state.user_data)}"""
                self.state.add_message("assistant", response)
                return response

            # Normal flow: parse environment input
            parsed = await parse_environment_input(user_input, self.state.user_data)

            # Check if parsing failed
            if not parsed and user_input.strip():
                from config import VALID_ENVIRONMENTS, AZURE_REGION_CODES
                env_list = ", ".join(VALID_ENVIRONMENTS[:8])
                region_list = ", ".join(list(AZURE_REGION_CODES.keys())[:8])
                response = f"""I couldn't understand the input. Please provide valid SDAF environment information.

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

Please try again!"""
                self.state.add_message("assistant", response)
                return response

            # PROGRESSIVE: Merge with existing data (skip empty/whitespace values)
            for key, value in parsed.items():
                if value and str(value).strip():
                    self.state.user_data[key] = str(value).strip()

            # Check what's still missing (strict validation: must be non-empty after strip)
            has_env = self.state.user_data.get("environment", "").strip()
            has_location = self.state.user_data.get("location", "").strip()
            has_network = self.state.user_data.get("network_logical_name", "").strip()

            # STRICT VALIDATION: All values must be present AND valid
            # Environment must be non-empty (min 2 chars)
            # Location must be non-empty
            # Network must be non-empty (min 3 chars, max 7 chars)
            env_valid = has_env and len(has_env) >= 2
            location_valid = has_location and len(has_location) >= 3
            network_valid = has_network and len(has_network) >= 3 and len(has_network) <= 7

            # ALL VALUES PRESENT AND VALID → Proceed
            if env_valid and location_valid and network_valid:
                self.state.current_prompt = 1
                response = get_prompt_message(1, self.state.user_data)
                self.state.add_message("assistant", response)
                return response

            # PARTIAL VALUES → Ask for missing
            missing = []
            if not env_valid:
                if not has_env:
                    missing.append("**Environment** (DEV, PROD, QA, UAT, TEST, SBX, LAB, etc.)")
                else:
                    missing.append(f"**Environment** (current: '{has_env}' - must be at least 2 chars)")
            if not location_valid:
                if not has_location:
                    missing.append("**Azure Region** (westeurope, eastus, northeurope, etc.)")
                else:
                    missing.append(f"**Azure Region** (current: '{has_location}' - must be at least 3 chars)")
            if not network_valid:
                if not has_network:
                    missing.append("**Network Name** (3-7 characters, alphanumeric)")
                elif len(has_network) < 3:
                    missing.append(f"**Network Name** (current: '{has_network}' - must be at least 3 chars)")
                elif len(has_network) > 7:
                    missing.append(f"**Network Name** (current: '{has_network}' - max 7 chars)")

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
            response += f"\n\n💡 You can provide everything at once or one at a time."

            self.state.add_message("assistant", response)
            return response

        # Prompt 1: SAP System Identity
        elif current_prompt == 1:
            parsed = await parse_sap_system_input(user_input, self.state.user_data)

            if not parsed and user_input.strip():
                response = """I couldn't understand the input. Please provide valid SAP System information.

**Requirements:**
- **SID**: Exactly 3 characters, alphanumeric, must start with a letter
  - ✅ Valid: X00, P01, S15, HDB
  - ❌ Invalid: X, 00X, SAP (reserved), X_0 (special characters)
- **Database Platform**: HANA, DB2, ORACLE, ASE, SQLSERVER, or NONE

**Examples:**
- "X00, HDB, HANA"
- "P01 ORA ORACLE"
- "sid X00, db HDB, platform HANA"

Please try again, or provide values one at a time!"""
                self.state.add_message("assistant", response)
                return response

            # PROGRESSIVE: Merge
            for key, value in parsed.items():
                if value:
                    self.state.user_data[key] = value

            # Check missing
            has_sid = self.state.user_data.get("sid")
            has_db_sid = self.state.user_data.get("database_sid")
            has_platform = self.state.user_data.get("database_platform")

            # ALL PRESENT → Proceed
            if has_sid and has_db_sid and has_platform:
                self.state.current_prompt = 2
                response = get_prompt_message(2, self.state.user_data)
                self.state.add_message("assistant", response)
                return response

            # PARTIAL → Ask for missing
            missing = []
            if not has_sid:
                missing.append("**SAP Application SID** (3 characters, alphanumeric, starts with letter)")
            if not has_db_sid:
                missing.append("**Database SID** (3 characters, alphanumeric, starts with letter)")
            if not has_platform:
                missing.append("**Database Platform** (HANA, DB2, ORACLE, ASE, SQLSERVER, NONE)")

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

            self.state.add_message("assistant", response)
            return response

        # Prompt 2: System Sizing
        elif current_prompt == 2:
            parsed = await parse_sizing_input(user_input)

            database_size = parsed.get("database_size", "Demo")
            purpose = parsed.get("purpose", "development")

            self.state.user_data["database_size"] = database_size
            self.state.user_data["app_tier_sizing_dictionary_key"] = parsed.get("app_tier_sizing", "Optimized")
            self.state.user_data["purpose"] = purpose
            self.state.user_data["size_description"] = database_size

            # AUTO-CONFIGURE for Demo/Small
            is_demo_or_small = any(keyword in database_size.lower() for keyword in ["demo", "s4demo"]) or \
                              any(keyword in purpose.lower() for keyword in ["demo", "test", "testing"])

            if is_demo_or_small:
                # Set standalone, no HA defaults
                self.state.user_data["enable_app_tier_deployment"] = False
                self.state.user_data["application_server_count"] = 0
                self.state.user_data["scs_server_count"] = 1
                self.state.user_data["database_server_count"] = 1
                self.state.user_data["database_high_availability"] = False
                self.state.user_data["scs_high_availability"] = False
                self.state.user_data["architecture_type"] = "standalone"
                self.state.user_data["ha_enabled"] = False

                # Skip Prompt 3 (Architecture) → Go to Prompt 4 (Network)
                self.state.current_prompt = 4
                response = f"""Perfect! Since this is a **{purpose}** system with **{database_size}** sizing, I've automatically configured it as:

✅ **Standalone Deployment** (everything on one server)
✅ **No High Availability** (single instance, cost-optimized)

This is the recommended configuration for Demo/Test/Development environments.

{get_prompt_message(4, self.state.user_data)}"""
                self.state.add_message("assistant", response)
                return response
            else:
                # Normal flow: continue to Prompt 3 (Architecture)
                self.state.current_prompt = 3
                response = get_prompt_message(3, self.state.user_data)
                self.state.add_message("assistant", response)
                return response

        # Prompt 3: Architecture Pattern
        elif current_prompt == 3:
            parsed = await parse_architecture_input(user_input)

            deployment_type = parsed.get("deployment_type", "standalone")
            ha_required = parsed.get("ha_required", False)
            app_count = parsed.get("application_server_count", 0)

            if deployment_type == "standalone":
                self.state.user_data["enable_app_tier_deployment"] = False
                self.state.user_data["application_server_count"] = 0
                self.state.user_data["scs_server_count"] = 1
                self.state.user_data["database_server_count"] = 1
                self.state.user_data["database_high_availability"] = False
                self.state.user_data["scs_high_availability"] = False
            else:  # distributed
                self.state.user_data["enable_app_tier_deployment"] = True
                self.state.user_data["application_server_count"] = app_count if app_count > 0 else 2

                if ha_required:
                    self.state.user_data["scs_server_count"] = 2
                    self.state.user_data["database_server_count"] = 2
                    self.state.user_data["database_high_availability"] = True
                    self.state.user_data["scs_high_availability"] = True
                else:
                    self.state.user_data["scs_server_count"] = 1
                    self.state.user_data["database_server_count"] = 1
                    self.state.user_data["database_high_availability"] = False
                    self.state.user_data["scs_high_availability"] = False

            self.state.user_data["architecture_type"] = deployment_type
            self.state.user_data["ha_enabled"] = ha_required

            self.state.current_prompt = 4
            response = get_prompt_message(4, self.state.user_data)
            self.state.add_message("assistant", response)
            return response

        # Prompt 4: Network Configuration
        elif current_prompt == 4:
            parsed = await parse_network_input(user_input)

            self.state.user_data["network_type"] = parsed.get("network_type", "greenfield")

            if parsed.get("custom_cidrs"):
                self.state.user_data["admin_subnet"] = parsed.get("admin_subnet", "10.1.0.0/24")
                self.state.user_data["db_subnet"] = parsed.get("db_subnet", "10.1.1.0/24")
                self.state.user_data["app_subnet"] = parsed.get("app_subnet", "10.1.2.0/24")
                self.state.user_data["web_subnet"] = parsed.get("web_subnet", "10.1.3.0/24")
            else:
                # Use defaults
                self.state.user_data["admin_subnet"] = "10.1.0.0/24"
                self.state.user_data["db_subnet"] = "10.1.1.0/24"
                self.state.user_data["app_subnet"] = "10.1.2.0/24"
                self.state.user_data["web_subnet"] = "10.1.3.0/24"

            self.state.current_prompt = 5
            response = get_prompt_message(5, self.state.user_data)
            self.state.add_message("assistant", response)
            return response

        # Prompt 5: Operating System
        elif current_prompt == 5:
            parsed = await parse_os_input(user_input)

            self.state.user_data["os_publisher"] = parsed.get("publisher", "SUSE")
            self.state.user_data["os_offer"] = parsed.get("offer", "sles-sap-15-sp5")
            self.state.user_data["os_sku"] = parsed.get("sku", "gen2")

            # Move to confirmation prompt
            self.state.current_prompt = 6
            response = generate_confirmation_summary(self.state.user_data)
            self.state.add_message("assistant", response)
            return response

        # Prompt 6: Confirmation
        elif current_prompt == 6:
            user_input_lower = user_input.lower().strip()

            # Check for confirmation
            if any(word in user_input_lower for word in ["ja", "yes", "confirm", "bestätigen", "korrekt", "richtig", "ok", "okay"]):
                # Generate tfvars
                self.state.tfvars_content = generate_tfvars(self.state.user_data)
                self.state.tfvars_ready = True
                self.state.current_prompt = 7

                filename = generate_sdaf_filename(self.state.user_data)
                response = generate_final_summary(self.state.user_data)
                self.state.add_message("assistant", response)
                return response

            # Check for rejection
            elif any(word in user_input_lower for word in ["nein", "no", "ändern", "edit", "korrigieren", "falsch", "change"]):
                response = """No problem! What would you like to change?

Just tell me which value should be corrected, e.g.:
- "Change Environment to PROD"
- "Region should be northeurope"
- "SID should be P01"

Or start a new chat to begin completely from scratch."""
                self.state.add_message("assistant", response)
                return response
            else:
                response = """Please confirm with **"yes"** if everything is correct, or say **"no"** if you want to change something.

You can also directly say what should be changed, e.g. "Change SID to P01"
"""
                self.state.add_message("assistant", response)
                return response

        else:
            response = "Configuration is complete! You can download the TFVARS file or start a new session."
            self.state.add_message("assistant", response)
            return response

    def get_tfvars(self) -> Optional[str]:
        """Get generated TFVARS content"""
        return self.state.tfvars_content

    def get_tfvars_filename(self) -> str:
        """Get SDAF-compliant filename"""
        return generate_sdaf_filename(self.state.user_data)

    def reset(self):
        """Reset agent state"""
        self.state = AgentState()


# Singleton instances (per session)
_agent_instances: Dict[str, SAPAgentV3] = {}


def get_agent(session_id: str) -> SAPAgentV3:
    """Get or create agent instance for session"""
    if session_id not in _agent_instances:
        _agent_instances[session_id] = SAPAgentV3()
    return _agent_instances[session_id]


def reset_agent(session_id: str):
    """Reset agent for session"""
    if session_id in _agent_instances:
        _agent_instances[session_id].reset()
