"""
Sizing Parser
=============

Parse sizing requirements from user input (Prompt 2).
Regex-first approach with numbered option support.
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional

from config import llm, LLM_TIMEOUT_SECONDS
from utils.normalizer import normalize_sizing, extract_number_selection, clean_input

logger = logging.getLogger(__name__)

# Numbered options mapping for sizing
SIZING_OPTIONS = {
    # Purpose options
    1: {"purpose": "demo", "database_size": "Demo"},
    2: {"purpose": "development", "database_size": "E20ds_v4"},
    3: {"purpose": "qa", "database_size": "E32ds_v4"},
    4: {"purpose": "production", "database_size": "E64ds_v5"},
    5: {"purpose": "production", "database_size": "M128s"},
}

# Size options mapping
SIZE_OPTIONS = {
    1: "Demo",
    2: "E20ds_v4",
    3: "E32ds_v4",
    4: "E64ds_v5",
    5: "M128s",
    6: "M208ms_v2",
}


def try_regex_parse_sizing(msg: str) -> Optional[Dict[str, Any]]:
    """Fast regex-first parsing for sizing input"""

    msg_clean = clean_input(msg)
    msg_lower = msg_clean.lower()

    # Check for numbered selection (1-6)
    num = extract_number_selection(msg_clean, 6)
    if num:
        if num in SIZE_OPTIONS:
            size = SIZE_OPTIONS[num]
            # Map size to purpose
            purpose_map = {
                "Demo": "demo",
                "E20ds_v4": "development",
                "E32ds_v4": "qa",
                "E64ds_v5": "production",
                "M128s": "production",
                "M208ms_v2": "production",
            }
            return {
                "database_size": size,
                "purpose": purpose_map.get(size, "development"),
                "app_tier_sizing": "Optimized"
            }

    # Use normalizer for keyword matching
    normalized = normalize_sizing(msg_lower)
    if normalized:
        return {
            "database_size": normalized["database_size"],
            "purpose": normalized["purpose"],
            "app_tier_sizing": "Optimized"
        }

    # Pattern: Memory-based - "256 GB", "1 TB", etc.
    memory_pattern = r'(\d+)\s*(gb|tb|gigabyte|terabyte)'
    match = re.search(memory_pattern, msg_lower)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        # Convert to GB
        if unit in ["tb", "terabyte"]:
            amount *= 1024

        # Map to size
        if amount <= 64:
            return {"database_size": "Demo", "purpose": "demo", "app_tier_sizing": "Optimized"}
        elif amount <= 200:
            return {"database_size": "E20ds_v4", "purpose": "development", "app_tier_sizing": "Optimized"}
        elif amount <= 300:
            return {"database_size": "E32ds_v4", "purpose": "qa", "app_tier_sizing": "Optimized"}
        elif amount <= 600:
            return {"database_size": "E64ds_v5", "purpose": "production", "app_tier_sizing": "Optimized"}
        elif amount <= 2048:
            return {"database_size": "M128s", "purpose": "production", "app_tier_sizing": "Optimized"}
        else:
            return {"database_size": "M208ms_v2", "purpose": "production", "app_tier_sizing": "Optimized"}

    # Pattern: Direct VM SKU - "E20ds_v4", "M128s", etc.
    sku_pattern = r'\b([EDM]\d+[dls]*s?_v\d+|M\d+[lms]*s?)\b'
    match = re.search(sku_pattern, msg, re.IGNORECASE)
    if match:
        sku = match.group(1)
        return {
            "database_size": sku,
            "purpose": "custom",
            "app_tier_sizing": "Optimized"
        }

    return None


async def parse_sizing_input(user_message: str) -> Dict[str, Any]:
    """Parse sizing requirements from user input with timeout"""

    # STAGE 1: Try fast regex parsing first
    regex_result = try_regex_parse_sizing(user_message)
    if regex_result:
        logger.info(f"Regex parsed sizing: {regex_result}")
        return regex_result

    # STAGE 2: Use LLM with timeout for complex input
    prompt = f"""Extract sizing information from this user input:
"{user_message}"

Expected information:
- purpose: demo/testing/development/qa/staging/production/high-load (normalize to lowercase)
- size_intent: demo/small/medium/large/xlarge/xxlarge

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
        logger.info(f"Using LLM for sizing: {user_message}")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout, using defaults for sizing")
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}
    except Exception as e:
        logger.error(f"Failed to parse sizing input: {e}")
        return {"purpose": "development", "database_size": "Demo", "app_tier_sizing": "Optimized"}
