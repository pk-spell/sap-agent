"""
Network Parser
==============

Parse network configuration from user input (Prompt 4).
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any

from config import llm, LLM_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


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
