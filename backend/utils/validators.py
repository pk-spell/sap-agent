"""
Input Validators
================

Validation functions for user inputs.
"""

import re
from typing import Optional, Tuple


def validate_sid(sid: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SAP SID format

    Rules:
    - Exactly 3 characters
    - Alphanumeric only
    - First character must be a letter
    - Cannot start with reserved prefixes (ADD, ALL, AMD, AND, ANY, ARE, ASC, AUX, AVG, BIT, CDC, COM, CON, DBA, END, EPS, FOR, GET, GID, IBM, INT, KEY, LOG, LPT, MAP, MAX, MIN, MON, NIX, NOT, NUL, OFF, OLD, OMS, OUT, PAD, PRN, RAW, REF, ROW, SAP, SET, SGA, SHG, SID, SQL, SUM, SYS, TMP, TOP, UID, USE, USR, VAR)

    Args:
        sid: SID to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not sid:
        return False, "SID cannot be empty"

    sid = sid.strip().upper()

    # Check length
    if len(sid) != 3:
        return False, f"SID must be exactly 3 characters (got {len(sid)})"

    # Check alphanumeric
    if not sid.isalnum():
        return False, "SID must contain only letters and numbers"

    # Check first character is letter
    if not sid[0].isalpha():
        return False, "SID must start with a letter"

    # Check for reserved words (common ones)
    reserved = [
        "ADD", "ALL", "AMD", "AND", "ANY", "ARE", "ASC", "AUX", "AVG",
        "BIT", "CDC", "COM", "CON", "DBA", "END", "EPS", "FOR", "GET",
        "GID", "IBM", "INT", "KEY", "LOG", "LPT", "MAP", "MAX", "MIN",
        "MON", "NIX", "NOT", "NUL", "OFF", "OLD", "OMS", "OUT", "PAD",
        "PRN", "RAW", "REF", "ROW", "SAP", "SET", "SGA", "SHG", "SID",
        "SQL", "SUM", "SYS", "TMP", "TOP", "UID", "USE", "USR", "VAR"
    ]

    if sid in reserved:
        return False, f"SID '{sid}' is a reserved keyword and cannot be used"

    return True, None


def validate_environment(env: str) -> Tuple[bool, Optional[str]]:
    """
    Validate environment name against SDAF whitelist

    Args:
        env: Environment name

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    from config import VALID_ENVIRONMENTS

    if not env:
        return False, "Environment cannot be empty"

    env = env.strip().upper()

    # Check if in whitelist
    if env not in VALID_ENVIRONMENTS:
        valid_list = ", ".join(VALID_ENVIRONMENTS[:10])  # Show first 10
        return False, f"Environment '{env}' not supported by SDAF. Valid: {valid_list}, ..."

    return True, None


def validate_network_name(network: str) -> Tuple[bool, Optional[str]]:
    """
    Validate network logical name

    Args:
        network: Network name

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not network:
        return False, "Network name cannot be empty"

    network = network.strip().upper()

    # Check length (max 7 chars for SDAF)
    if len(network) > 7:
        return False, f"Network name too long (max 7 chars, got {len(network)})"

    # Check alphanumeric
    if not network.isalnum():
        return False, "Network name must contain only letters and numbers"

    return True, None


def normalize_and_validate_sid(sid: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize and validate SID in one step

    Args:
        sid: SID to normalize and validate

    Returns:
        Tuple[Optional[str], Optional[str]]: (normalized_sid, error_message)
    """
    if not sid:
        return None, "SID cannot be empty"

    normalized = sid.strip().upper()
    is_valid, error = validate_sid(normalized)

    if is_valid:
        return normalized, None
    else:
        return None, error


def validate_database_platform(platform: str) -> Tuple[bool, Optional[str]]:
    """
    Validate database platform against SDAF whitelist

    Args:
        platform: Database platform name

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    from config import VALID_DB_PLATFORMS

    if not platform:
        return False, "Database platform cannot be empty"

    platform_upper = platform.strip().upper()

    if platform_upper not in VALID_DB_PLATFORMS:
        return False, f"Invalid database platform '{platform}'. Must be one of: {', '.join(VALID_DB_PLATFORMS)}"

    return True, None
