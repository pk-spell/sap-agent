"""
Helper Utilities
================

Common helper functions for region codes, validation, etc.
"""

import logging
from typing import Optional
from config import AZURE_REGION_CODES

logger = logging.getLogger(__name__)


def validate_azure_region(region: str) -> Optional[str]:
    """
    Validate and normalize Azure region name

    Args:
        region: Region name to validate (case-insensitive)

    Returns:
        str: Normalized lowercase region name if valid, None otherwise
    """
    region_lower = region.lower().strip()

    # Direct match
    if region_lower in AZURE_REGION_CODES:
        return region_lower

    # Try matching common aliases
    aliases = {
        "west europe": "westeurope",
        "north europe": "northeurope",
        "east us": "eastus",
        "west us": "westus",
        "central us": "centralus",
        "germany west central": "germanywestcentral",
        "uk south": "uksouth",
        "france central": "francecentral"
    }

    if region_lower in aliases:
        return aliases[region_lower]

    return None


def get_region_code(region: str) -> str:
    """
    Get the short region code for a given Azure region

    Args:
        region: Full region name (e.g., "westeurope")

    Returns:
        str: Region code (e.g., "WEEU") or uppercase region if not found
    """
    return AZURE_REGION_CODES.get(region.lower(), region.upper()[:4])


def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())[:8]
