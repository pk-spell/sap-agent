"""
Sizing Parser
=============

Parse sizing requirements from user input (Prompt 2).
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any

from config import llm, LLM_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


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
