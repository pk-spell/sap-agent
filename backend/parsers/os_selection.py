"""
OS Selection Parser
===================

Parse operating system selection from user input (Prompt 5).
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any

from config import llm, LLM_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


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
