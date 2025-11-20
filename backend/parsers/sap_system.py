"""
SAP System Parser
=================

Parse SAP system identity from user input (Prompt 1).
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional

from config import llm, LLM_TIMEOUT_SECONDS
from utils.validators import (
    validate_sid,
    validate_database_platform,
    normalize_and_validate_sid
)

logger = logging.getLogger(__name__)


def try_regex_parse_sap_system(msg: str, existing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Context-aware parsing - doesn't overwrite already set values"""

    has_sid = existing_data.get("sid")
    has_db_sid = existing_data.get("database_sid")
    has_platform = existing_data.get("database_platform")

    # Pattern 1: "X00 HDB HANA" (all 3 values)
    pattern1 = r'^\s*([A-Z0-9]{3})\s+([A-Z0-9]{3})\s+(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)\s*$'
    match = re.search(pattern1, msg, re.IGNORECASE)
    if match:
        sid = match.group(1).upper()
        db_sid = match.group(2).upper()
        platform = match.group(3).upper()

        # Validate SIDs
        sid_valid, sid_error = validate_sid(sid)
        db_sid_valid, db_sid_error = validate_sid(db_sid)

        if not sid_valid:
            logger.warning(f"Invalid SID '{sid}': {sid_error}")
            return {}
        if not db_sid_valid:
            logger.warning(f"Invalid DB SID '{db_sid}': {db_sid_error}")
            return {}

        logger.info("✅ Regex: 3 values space-separated (validated)")
        return {
            "sid": sid,
            "database_sid": db_sid,
            "database_platform": platform
        }

    # Pattern 2: "X00, HDB, HANA" (comma-separated)
    pattern2 = r'^\s*([A-Z0-9]{3})\s*,\s*([A-Z0-9]{3})\s*,\s*(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)\s*$'
    match = re.search(pattern2, msg, re.IGNORECASE)
    if match:
        sid = match.group(1).upper()
        db_sid = match.group(2).upper()
        platform = match.group(3).upper()

        # Validate
        sid_valid, sid_error = validate_sid(sid)
        db_sid_valid, db_sid_error = validate_sid(db_sid)

        if not sid_valid:
            logger.warning(f"Invalid SID '{sid}': {sid_error}")
            return {}
        if not db_sid_valid:
            logger.warning(f"Invalid DB SID '{db_sid}': {db_sid_error}")
            return {}

        logger.info("✅ Regex: 3 values comma-separated (validated)")
        return {
            "sid": sid,
            "database_sid": db_sid,
            "database_platform": platform
        }

    # Pattern 3: "SID X00, DB HDB, platform HANA" (labeled)
    pattern3 = r'(?:sid\s*:?\s*)?([A-Z0-9]{3}).*?(?:db|database).*?([A-Z0-9]{3}).*?(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)'
    match = re.search(pattern3, msg, re.IGNORECASE)
    if match:
        logger.info("✅ Regex: labeled format")
        return {
            "sid": match.group(1).upper(),
            "database_sid": match.group(2).upper(),
            "database_platform": match.group(3).upper()
        }

    # PARTIAL: Two 3-char codes "X00 HDB" or "X00, HDB"
    pattern_two = r'^\s*([A-Z0-9]{3})\s*[,\s]+\s*([A-Z0-9]{3})\s*$'
    match = re.search(pattern_two, msg, re.IGNORECASE)
    if match:
        code1 = match.group(1).upper()
        code2 = match.group(2).upper()

        if not has_sid and not has_db_sid:
            # Neither set → assume SID + DB_SID
            logger.info("✅ Regex: SID + DB_SID")
            return {"sid": code1, "database_sid": code2}
        elif has_sid and not has_db_sid:
            # SID already set → both are DB_SID (second overwrites first)
            logger.info("✅ Regex: DB_SID update")
            return {"database_sid": code2}

    # PARTIAL: Single 3-char code "X00" or "HDB"
    pattern_single = r'^\s*([A-Z0-9]{3})\s*$'
    match = re.search(pattern_single, msg, re.IGNORECASE)
    if match:
        code = match.group(1).upper()

        # Validate SID format
        is_valid, error = validate_sid(code)
        if not is_valid:
            logger.warning(f"Invalid SID '{code}': {error}")
            return {}

        # Context-aware: fill first missing slot
        if not has_sid:
            logger.info(f"✅ Regex: Setting SID = {code} (validated)")
            return {"sid": code}
        elif not has_db_sid:
            logger.info(f"✅ Regex: Setting DB_SID = {code} (validated)")
            return {"database_sid": code}
        else:
            # Both already set, ignore
            logger.info(f"⚠️ SID and DB_SID already set, ignoring '{code}'")
            return {}

    # PARTIAL: Platform only "HANA" or "ORACLE"
    pattern_platform = r'^\s*(HANA|DB2|ORACLE|ASE|SQLSERVER|NONE)\s*$'
    match = re.search(pattern_platform, msg, re.IGNORECASE)
    if match:
        if not has_platform:
            logger.info("✅ Regex: Platform only")
            return {"database_platform": match.group(1).upper()}
        else:
            logger.info(f"⚠️ Platform already set, ignoring")
            return {}

    return None


async def parse_sap_system_input(user_message: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse SAP system identity using Hybrid approach (Regex → LLM with timeout)"""

    # STAGE 1: Try fast regex parsing first (context-aware)
    regex_result = try_regex_parse_sap_system(user_message, existing_data)
    if regex_result:
        return regex_result

    # STAGE 2: Use LLM with timeout
    prompt = f"""Extract SAP system parameters from this user input:
"{user_message}"

Expected parameters:
- sid: SAP Application SID (3 uppercase chars, like X00, P01)
- database_sid: Database SID (3 chars, like HDB, XDB, ORA)
- database_platform: Database type (must be one of: HANA, DB2, ORACLE, ASE, SQLSERVER, NONE)

Return ONLY a valid JSON object like:
{{"sid": "X00", "database_sid": "HDB", "database_platform": "HANA"}}

If you cannot extract a parameter, use null.
"""

    try:
        logger.info(f"⏱️ Using LLM for SAP system input (timeout: {LLM_TIMEOUT_SECONDS}s)")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout after {LLM_TIMEOUT_SECONDS}s")
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to parse SAP system input: {e}")
        return {}
