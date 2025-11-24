"""
Environment Parser
==================

Parse environment configuration from user input (Prompt 0).
"""

import re
import json
import logging
import asyncio
from typing import Dict, Any, Optional

from config import llm, LLM_TIMEOUT_SECONDS, VALID_ENVIRONMENTS
from utils.helpers import validate_azure_region
from utils.validators import validate_environment, validate_network_name

logger = logging.getLogger(__name__)


def try_regex_parse_environment(msg: str, existing_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Fast regex parsing for environment input with partial support and context awareness"""

    existing_data = existing_data or {}
    has_env = existing_data.get("environment")
    has_location = existing_data.get("location")
    has_network = existing_data.get("network_logical_name")

    # FULL PATTERNS - All 3 values

    # Pattern 1: "DEV, westeurope, SAP01"
    pattern1 = r'^\s*(\w+)\s*[,/]\s*([\w\s-]+?)\s*[,/]\s*(\w+)\s*$'
    match = re.search(pattern1, msg, re.IGNORECASE)
    if match:
        env = match.group(1).upper()[:5]
        region = validate_azure_region(match.group(2))
        network = match.group(3).upper()[:7]

        # Validate each component
        env_valid, env_error = validate_environment(env)
        network_valid, network_error = validate_network_name(network)

        if not env_valid or not region or not network_valid:
            logger.warning(f"Validation failed: env={env_error}, region={region}, network={network_error}")
            return {}

        if region:
            logger.info("✅ Regex: comma/slash - all 3 (validated)")
            return {
                "environment": env,
                "location": region,
                "network_logical_name": network
            }

    # Pattern 2: "DEV westeurope SAP01"
    pattern2 = r'^\s*(\w+)\s+([\w\s-]+?)\s+(\w+)\s*$'
    match = re.search(pattern2, msg, re.IGNORECASE)
    if match:
        region = validate_azure_region(match.group(2))
        if region:
            logger.info("✅ Regex: space - all 3")
            return {
                "environment": match.group(1).upper()[:5],
                "location": region,
                "network_logical_name": match.group(3).upper()[:7]
            }

    # Pattern 3a: "dev in westeurope SAP01" (with network)
    pattern3a = r'(\w+)\s+in\s+([\w\s-]+?)\s+(?:network\s*:?\s*)?(\w+)$'
    match = re.search(pattern3a, msg, re.IGNORECASE)
    if match:
        region = validate_azure_region(match.group(2).strip())
        if region:
            env_valid, _ = validate_environment(match.group(1).upper())
            network_valid, _ = validate_network_name(match.group(3).upper())
            if env_valid and network_valid:
                logger.info("✅ Regex: 'in' keyword - all 3")
                return {
                    "environment": match.group(1).upper()[:5],
                    "location": region,
                    "network_logical_name": match.group(3).upper()[:7]
                }

    # Pattern 3b: "dev in westeurope" (without network)
    pattern3b = r'^(\w+)\s+in\s+([\w\s-]+?)$'
    match = re.search(pattern3b, msg, re.IGNORECASE)
    if match:
        region = validate_azure_region(match.group(2).strip())
        env_valid, _ = validate_environment(match.group(1).upper())
        if region and env_valid:
            logger.info("✅ Regex: 'in' keyword - env + region only")
            return {
                "environment": match.group(1).upper()[:5],
                "location": region
            }

    # PARTIAL PATTERNS - Support progressive input (CONTEXT-AWARE)

    # Pattern 4: Single word - could be ENV, REGION, or NETWORK depending on context
    pattern_single = r'^\s*(\w+)\s*$'
    match = re.search(pattern_single, msg, re.IGNORECASE)
    if match:
        word = match.group(1).upper()

        # Try as environment first (if not set)
        # Accept any alphanumeric word (max 5 chars), not just VALID_ENVIRONMENTS
        if not has_env:
            env_valid, env_error = validate_environment(word)
            if env_valid:
                logger.info(f"✅ Regex: Environment only = {word}")
                return {"environment": word[:5]}

        # Try as region (if env is set but location isn't)
        if has_env and not has_location:
            region = validate_azure_region(msg)
            if region:
                logger.info(f"✅ Regex: Region only = {region}")
                return {"location": region}

        # Otherwise treat as network name (if env and location are set)
        if has_env and has_location and not has_network:
            network_valid, network_error = validate_network_name(word)
            if network_valid:
                logger.info(f"✅ Regex: Network name only = {word}")
                return {"network_logical_name": word[:7]}

    # Pattern 5: Two words - could be "ENV REGION" or "REGION NETWORK"
    pattern_two = r'^\s*(\S+)\s+(\S+)\s*$'
    match = re.search(pattern_two, msg, re.IGNORECASE)
    if match:
        word1 = match.group(1).upper()
        word2 = match.group(2)

        # Try "ENV REGION"
        if not has_env:
            env_valid, _ = validate_environment(word1)
            if env_valid:
                region = validate_azure_region(word2)
                if region:
                    logger.info("✅ Regex: Env + Region")
                    return {
                        "environment": word1[:5],
                        "location": region
                    }

        # Try "REGION NETWORK" (if env already set)
        if has_env and not has_location:
            region = validate_azure_region(word1)
            if region:
                network_valid, _ = validate_network_name(word2.upper())
                if network_valid:
                    logger.info("✅ Regex: Region + Network")
                    return {
                        "location": region,
                        "network_logical_name": word2.upper()[:7]
                    }

    # Pattern 6: Natural language - extract keywords
    # "x ist mein env und westeurope meine region zudem ist SAP02 mein netzwerkname"
    if not has_env or not has_location or not has_network:
        # Extract potential values from natural language
        words = msg.split()
        result = {}

        # Track what we've found to avoid double-matching
        env_found = has_env
        location_found = has_location
        network_found = has_network

        for i, word in enumerate(words):
            word_upper = word.upper().strip('.,;:')

            # Skip common filler words
            if word_upper in ["IN", "IST", "MEIN", "UND", "ZUDEM", "ENV", "REGION", "NETWORK", "THE", "AND", "MY", "IS"]:
                continue

            # Priority 1: Check if it's a region (most specific)
            if not location_found:
                region = validate_azure_region(word)
                if region:
                    result["location"] = region
                    location_found = True
                    logger.info(f"✅ Natural language: Found region = {region}")
                    continue  # Skip to next word

            # Priority 2: Check if it's a valid environment (if not already found)
            if not env_found and len(word_upper) <= 5:
                env_valid, _ = validate_environment(word_upper)
                if env_valid:
                    result["environment"] = word_upper
                    env_found = True
                    logger.info(f"✅ Natural language: Found environment = {word_upper}")
                    continue  # Skip to next word

            # Priority 3: Check if it's a network name (only if env and location are set/found)
            if (env_found or location_found) and not network_found and len(word_upper) <= 7:
                network_valid, _ = validate_network_name(word_upper)
                if network_valid:
                    result["network_logical_name"] = word_upper
                    network_found = True
                    logger.info(f"✅ Natural language: Found network = {word_upper}")

        if result:
            logger.info("✅ Natural language parsing succeeded")
            return result

    logger.info("ℹ️ No regex pattern matched")
    return None


async def parse_environment_input(user_message: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Parse environment input using Hybrid approach (Regex → LLM with timeout)"""

    existing_data = existing_data or {}

    # STAGE 1: Try fast regex parsing first (with context)
    regex_result = try_regex_parse_environment(user_message, existing_data)
    if regex_result:
        return regex_result

    # STAGE 2: Use LLM with timeout for complex input
    prompt = f"""Extract SAP deployment parameters from this user input:
"{user_message}"

Expected parameters:
- environment: DEV/PROD/QA/NONPROD/etc (normalize to uppercase, max 5 chars)
- location: Azure region (westeurope, eastus, northeurope, etc)
- network_logical_name: Network identifier (max 7 chars, uppercase)

Return ONLY a valid JSON object like:
{{"environment": "DEV", "location": "westeurope", "network_logical_name": "SAP01"}}

If you cannot extract a parameter, use null.
"""

    try:
        logger.info(f"⏱️ Using LLM for complex environment input (timeout: {LLM_TIMEOUT_SECONDS}s)")
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=LLM_TIMEOUT_SECONDS
        )
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ LLM timeout after {LLM_TIMEOUT_SECONDS}s for input: {user_message}")
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to parse environment input: {e}")
        return {}
