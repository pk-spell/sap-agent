"""
Network Parser
==============

Parse network configuration from user input (Prompt 4).
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

# Numbered options mapping for network type
NETWORK_OPTIONS = {
    1: {"network_type": "greenfield", "custom_cidrs": False},
    2: {"network_type": "brownfield", "custom_cidrs": False},
}

# Default subnet CIDRs
DEFAULT_SUBNETS = {
    "admin_subnet": "10.1.0.0/24",
    "db_subnet": "10.1.1.0/24",
    "app_subnet": "10.1.2.0/24",
    "web_subnet": "10.1.3.0/24",
}


def try_regex_parse_network(msg: str) -> Optional[Dict[str, Any]]:
    """Fast regex-first parsing for network input"""

    msg_clean = clean_input(msg)
    msg_lower = msg_clean.lower()

    # Check for numbered selection (1-2)
    num = extract_number_selection(msg_clean, 2)
    if num and num in NETWORK_OPTIONS:
        logger.info(f"Network parsed by number: {num}")
        result = NETWORK_OPTIONS[num].copy()
        result.update(DEFAULT_SUBNETS)
        return result

    # Pattern: Greenfield keywords
    greenfield_keywords = ["greenfield", "green field", "new", "neu", "default", "defaults", "standard"]
    if any(kw in msg_lower for kw in greenfield_keywords):
        logger.info("Network parsed as greenfield via keyword")
        return {
            "network_type": "greenfield",
            "custom_cidrs": False,
            **DEFAULT_SUBNETS
        }

    # Pattern: Brownfield keywords
    brownfield_keywords = ["brownfield", "brown field", "existing", "bestehend", "vorhanden"]
    if any(kw in msg_lower for kw in brownfield_keywords):
        logger.info("Network parsed as brownfield via keyword")
        return {
            "network_type": "brownfield",
            "custom_cidrs": False,
            **DEFAULT_SUBNETS
        }

    # Pattern: Accept/OK/Yes/Fine keywords (accept defaults)
    accept_keywords = ["ok", "okay", "yes", "ja", "fine", "gut", "accept", "akzeptieren", "defaults are fine"]
    if any(kw in msg_lower for kw in accept_keywords):
        logger.info("Network: User accepted defaults")
        return {
            "network_type": "greenfield",
            "custom_cidrs": False,
            **DEFAULT_SUBNETS
        }

    # Pattern: Custom CIDR detection - "10.x.x.x" or "use 10.10.x.x range"
    cidr_pattern = r'(\d{1,3}\.\d{1,3})\.'
    match = re.search(cidr_pattern, msg)
    if match:
        base = match.group(1)  # e.g., "10.10"
        logger.info(f"Network: Custom CIDR base detected: {base}")
        return {
            "network_type": "greenfield",
            "custom_cidrs": True,
            "admin_subnet": f"{base}.0.0/24",
            "db_subnet": f"{base}.1.0/24",
            "app_subnet": f"{base}.2.0/24",
            "web_subnet": f"{base}.3.0/24",
        }

    # Pattern: Full CIDR notation - "10.10.0.0/24"
    full_cidr_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})'
    cidrs = re.findall(full_cidr_pattern, msg)
    if cidrs:
        logger.info(f"Network: Full CIDRs detected: {cidrs}")
        result = {
            "network_type": "greenfield",
            "custom_cidrs": True,
        }
        # Assign CIDRs in order: admin, db, app, web
        subnet_keys = ["admin_subnet", "db_subnet", "app_subnet", "web_subnet"]
        for i, cidr in enumerate(cidrs[:4]):
            result[subnet_keys[i]] = cidr
        # Fill remaining with defaults
        for key in subnet_keys[len(cidrs):]:
            result[key] = DEFAULT_SUBNETS[key]
        return result

    return None


async def parse_network_input(user_message: str) -> Dict[str, Any]:
    """Parse network configuration from user input with timeout"""

    # STAGE 1: Try fast regex parsing first
    regex_result = try_regex_parse_network(user_message)
    if regex_result:
        logger.info(f"Regex parsed network: {regex_result}")
        return regex_result

    # STAGE 2: Use LLM with timeout for complex input
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
        logger.info(f"Using LLM for network: {user_message}")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # Add default subnets if not custom
            if not result.get("custom_cidrs"):
                result.update(DEFAULT_SUBNETS)
            return result
        return {"network_type": "greenfield", "custom_cidrs": False, **DEFAULT_SUBNETS}
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout, using greenfield defaults")
        return {"network_type": "greenfield", "custom_cidrs": False, **DEFAULT_SUBNETS}
    except Exception as e:
        logger.error(f"Failed to parse network input: {e}")
        return {"network_type": "greenfield", "custom_cidrs": False, **DEFAULT_SUBNETS}
