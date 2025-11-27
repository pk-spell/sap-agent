"""
Architecture Parser
===================

Parse architecture pattern from user input (Prompt 3).
Regex-first approach with numbered option support.
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional

from config import llm, LLM_TIMEOUT_SECONDS
from utils.normalizer import extract_number_selection, clean_input

logger = logging.getLogger(__name__)

# Numbered options mapping for deployment type
DEPLOYMENT_OPTIONS = {
    1: {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0},
    2: {"deployment_type": "distributed", "ha_required": False, "application_server_count": 2},
}

# Numbered options for HA
HA_OPTIONS = {
    1: False,  # No HA
    2: True,   # With HA
}


def try_regex_parse_architecture(msg: str) -> Optional[Dict[str, Any]]:
    """Fast regex-first parsing for architecture input"""

    msg_clean = clean_input(msg)
    msg_lower = msg_clean.lower()

    # Check for numbered selection (1-2) for deployment type
    num = extract_number_selection(msg_clean, 2)
    if num and num in DEPLOYMENT_OPTIONS:
        logger.info(f"Architecture parsed by number: {num}")
        return DEPLOYMENT_OPTIONS[num].copy()

    # Pattern: Standalone keywords
    standalone_keywords = ["standalone", "stand alone", "single", "einzeln", "alles auf einem", "one server", "ein server"]
    if any(kw in msg_lower for kw in standalone_keywords):
        logger.info("Architecture parsed as standalone via keyword")
        return {
            "deployment_type": "standalone",
            "ha_required": False,
            "application_server_count": 0
        }

    # Pattern: Distributed keywords
    distributed_keywords = ["distributed", "verteilt", "separate", "getrennt", "multi-server", "multiserver"]
    is_distributed = any(kw in msg_lower for kw in distributed_keywords)

    # Pattern: HA keywords
    ha_keywords = ["ha", "high availability", "hochverfügbar", "cluster", "clustering", "failover", "zero-downtime"]
    no_ha_keywords = ["no ha", "ohne ha", "single instance", "kein ha", "no high availability"]

    ha_required = False
    if any(kw in msg_lower for kw in ha_keywords):
        ha_required = True
    if any(kw in msg_lower for kw in no_ha_keywords):
        ha_required = False

    # Pattern: App server count - "2 app servers", "with 3 application servers"
    app_count_pattern = r'(\d+)\s*(?:app(?:lication)?\s*server|as)'
    match = re.search(app_count_pattern, msg_lower)
    app_count = int(match.group(1)) if match else (2 if is_distributed else 0)

    # If distributed mentioned explicitly
    if is_distributed:
        logger.info(f"Architecture parsed as distributed via keyword (HA: {ha_required}, apps: {app_count})")
        return {
            "deployment_type": "distributed",
            "ha_required": ha_required,
            "application_server_count": app_count if app_count > 0 else 2
        }

    # Pattern: Combined - "distributed with 2 app servers, no HA"
    combined_pattern = r'(standalone|distributed)(?:\s+with\s+(\d+)\s+app)?(?:.*?(no\s+ha|with\s+ha))?'
    match = re.search(combined_pattern, msg_lower)
    if match:
        deployment = match.group(1)
        count = int(match.group(2)) if match.group(2) else (0 if deployment == "standalone" else 2)
        ha = match.group(3)
        ha_required = ha == "with ha" if ha else False

        logger.info(f"Architecture: Combined pattern - {deployment}, count={count}, ha={ha_required}")
        return {
            "deployment_type": deployment,
            "ha_required": ha_required,
            "application_server_count": count
        }

    # Pattern: Simple number for HA choice (when already in HA question context)
    # This would be used if we split the questions
    if msg_clean.strip() in ["1", "2"]:
        # This is handled above with DEPLOYMENT_OPTIONS
        pass

    # Pattern: Accept defaults - for dev/test use standalone
    accept_keywords = ["ok", "okay", "yes", "ja", "fine", "gut", "simple", "einfach", "default"]
    if any(kw in msg_lower for kw in accept_keywords):
        logger.info("Architecture: User accepted defaults (standalone)")
        return {
            "deployment_type": "standalone",
            "ha_required": False,
            "application_server_count": 0
        }

    return None


async def parse_architecture_input(user_message: str) -> Dict[str, Any]:
    """Parse architecture pattern from user input with timeout"""

    # STAGE 1: Try fast regex parsing first
    regex_result = try_regex_parse_architecture(user_message)
    if regex_result:
        logger.info(f"Regex parsed architecture: {regex_result}")
        return regex_result

    # STAGE 2: Use LLM with timeout for complex input
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
        logger.info(f"Using LLM for architecture: {user_message}")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout, using standalone defaults")
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}
    except Exception as e:
        logger.error(f"Failed to parse architecture input: {e}")
        return {"deployment_type": "standalone", "ha_required": False, "application_server_count": 0}
