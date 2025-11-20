"""
Helper Functions
================

Utility functions for the frontend.
"""

import re
from datetime import datetime


def extract_sid_from_content(tfvars: str) -> str:
    """
    Extract SID from tfvars content for filename

    Args:
        tfvars: The tfvars file content

    Returns:
        str: Extracted SID or timestamp-based fallback
    """
    # Try to find sid = "XXX" pattern
    match = re.search(r'sid\s*=\s*"(\w+)"', tfvars)
    if match:
        return match.group(1)

    # Fallback to timestamp-based name
    return f"sap_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def generate_sdaf_filename(user_data: dict) -> str:
    """
    Generate SDAF-compliant filename: ENV-REGION_CODE-NETWORK-SID.tfvars

    Examples:
    - PRD-WEEU-SAP01-X00.tfvars
    - DEV-NOEU-SAP02-P01.tfvars

    Args:
        user_data: Dictionary with environment, location, network_logical_name, sid

    Returns:
        str: SDAF-compliant filename
    """
    # Region code mapping (short codes)
    region_codes = {
        "westeurope": "WEEU",
        "northeurope": "NOEU",
        "eastus": "EAUS",
        "eastus2": "EUS2",
        "westus": "WEUS",
        "westus2": "WUS2",
        "westus3": "WUS3",
        "centralus": "CEUS",
        "northcentralus": "NCUS",
        "southcentralus": "SCUS",
        "germanywestcentral": "DEWC",
        "francecentral": "FRCE",
        "uksouth": "UKSO",
        "ukwest": "UKWE",
        "switzerlandnorth": "SZNO",
        "norwayeast": "NOEA",
        "swedencentral": "SECE"
    }

    env = user_data.get("environment", "DEV").upper()[:5]
    location = user_data.get("location", "westeurope").lower()
    region_code = region_codes.get(location, location[:4].upper())
    network = user_data.get("network_logical_name", "SAP01").upper()[:7]
    sid = user_data.get("sid", "X00").upper()

    return f"{env}-{region_code}-{network}-{sid}.tfvars"
