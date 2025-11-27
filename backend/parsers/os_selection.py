"""
OS Selection Parser
===================

Parse operating system selection from user input (Prompt 5).
Regex-first approach with numbered option support.
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional

from config import llm, LLM_TIMEOUT_SECONDS
from utils.normalizer import normalize_os, extract_number_selection, clean_input

logger = logging.getLogger(__name__)

# Numbered options mapping for OS selection
OS_OPTIONS = {
    # SUSE options
    1: {"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"},
    2: {"publisher": "SUSE", "offer": "sles-sap-15-sp4", "sku": "gen2"},
    3: {"publisher": "SUSE", "offer": "sles-sap-15-sp3", "sku": "gen2"},
    4: {"publisher": "SUSE", "offer": "sles-sap-12-sp5", "sku": "gen2"},
    # Red Hat options
    5: {"publisher": "RedHat", "offer": "RHEL-SAP-HA", "sku": "9_0"},
    6: {"publisher": "RedHat", "offer": "RHEL-SAP-HA", "sku": "8.6"},
    7: {"publisher": "RedHat", "offer": "RHEL-SAP-HA", "sku": "8.4"},
}

# Default OS
DEFAULT_OS = {"publisher": "SUSE", "offer": "sles-sap-15-sp5", "sku": "gen2"}


def try_regex_parse_os(msg: str) -> Optional[Dict[str, str]]:
    """Fast regex-first parsing for OS input"""

    msg_clean = clean_input(msg)
    msg_lower = msg_clean.lower()

    # Check for numbered selection (1-7)
    num = extract_number_selection(msg_clean, 7)
    if num and num in OS_OPTIONS:
        logger.info(f"OS parsed by number: {num}")
        return OS_OPTIONS[num]

    # Use normalizer for keyword matching (handles typos)
    normalized = normalize_os(msg_lower)
    if normalized:
        logger.info(f"OS normalized: {normalized}")
        return normalized

    # Pattern: Direct offer name - "sles-sap-15-sp5", "RHEL-SAP-HA"
    sles_pattern = r'sles[-\s]*(?:sap)?[-\s]*(\d+)[-\s]*sp(\d+)'
    match = re.search(sles_pattern, msg_lower)
    if match:
        version = match.group(1)
        sp = match.group(2)
        return {
            "publisher": "SUSE",
            "offer": f"sles-sap-{version}-sp{sp}",
            "sku": "gen2"
        }

    rhel_pattern = r'rhel[-\s]*(?:sap)?[-\s]*(\d+)(?:\.(\d+))?'
    match = re.search(rhel_pattern, msg_lower)
    if match:
        major = match.group(1)
        minor = match.group(2) or "0"
        if major == "9":
            sku = "9_0"
        elif major == "8":
            if minor in ["6", "4", "2"]:
                sku = f"8.{minor}"
            else:
                sku = "8.6"
        else:
            sku = "7.9"
        return {
            "publisher": "RedHat",
            "offer": "RHEL-SAP-HA",
            "sku": sku
        }

    return None


async def parse_os_input(user_message: str) -> Dict[str, Any]:
    """Parse operating system selection from user input with timeout"""

    # STAGE 1: Try fast regex parsing first
    regex_result = try_regex_parse_os(user_message)
    if regex_result:
        logger.info(f"Regex parsed OS: {regex_result}")
        return regex_result

    # STAGE 2: Use LLM with timeout for complex input
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
        logger.info(f"Using LLM for OS: {user_message}")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        # Default to SLES 15 SP5
        return DEFAULT_OS
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout, using SLES 15 SP5 default")
        return DEFAULT_OS
    except Exception as e:
        logger.error(f"Failed to parse OS input: {e}")
        return DEFAULT_OS
