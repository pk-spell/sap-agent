"""
Architecture Parser
===================

Parse architecture pattern from user input (Prompt 3).
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any

from config import llm, LLM_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


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
