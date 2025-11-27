"""
Input Normalizer
================

Normalize and correct user inputs for better UX.
Handles case normalization, typo correction, and common variations.
"""

import re
from typing import Optional, Dict, List, Tuple

# Common typos and variations for Azure regions
REGION_TYPOS: Dict[str, str] = {
    # West Europe variations
    "westeuropa": "westeurope",
    "west europa": "westeurope",
    "west-europe": "westeurope",
    "west_europe": "westeurope",
    "we": "westeurope",
    "weeu": "westeurope",
    "europe west": "westeurope",
    "europa west": "westeurope",

    # North Europe variations
    "northeuropa": "northeurope",
    "north europa": "northeurope",
    "north-europe": "northeurope",
    "north_europe": "northeurope",
    "ne": "northeurope",
    "noeu": "northeurope",
    "europe north": "northeurope",

    # East US variations
    "east-us": "eastus",
    "east_us": "eastus",
    "us east": "eastus",
    "useast": "eastus",
    "eus": "eastus",

    # West US variations
    "west-us": "westus",
    "west_us": "westus",
    "us west": "westus",
    "uswest": "westus",
    "wus": "westus",

    # Germany variations
    "germany": "germanywestcentral",
    "deutschland": "germanywestcentral",
    "de": "germanywestcentral",
    "dewc": "germanywestcentral",
    "germany west": "germanywestcentral",
    "germany-west-central": "germanywestcentral",

    # France variations
    "france": "francecentral",
    "frankreich": "francecentral",
    "fr": "francecentral",
    "frce": "francecentral",
    "france-central": "francecentral",

    # UK variations
    "uk": "uksouth",
    "ukso": "uksouth",
    "uk-south": "uksouth",
    "uk_south": "uksouth",
    "england": "uksouth",

    # Switzerland variations
    "switzerland": "switzerlandnorth",
    "schweiz": "switzerlandnorth",
    "ch": "switzerlandnorth",
    "szno": "switzerlandnorth",
}

# Common typos for environments
ENVIRONMENT_TYPOS: Dict[str, str] = {
    # DEV variations
    "development": "DEV",
    "develop": "DEV",
    "devel": "DEV",
    "dev": "DEV",
    "entwicklung": "DEV",

    # PROD variations
    "production": "PROD",
    "produktiv": "PROD",
    "prod": "PROD",
    "prd": "PRD",
    "live": "PROD",

    # QA variations
    "quality": "QA",
    "qualitaet": "QA",
    "test": "TEST",
    "testing": "TEST",
    "tst": "TEST",

    # Other
    "sandbox": "SBX",
    "sbx": "SBX",
    "demo": "DEMO",
    "labor": "LAB",
    "lab": "LAB",
}

# Common typos for database platforms
PLATFORM_TYPOS: Dict[str, str] = {
    "hana": "HANA",
    "sap hana": "HANA",
    "saphana": "HANA",
    "h4": "HANA",

    "oracle": "ORACLE",
    "ora": "ORACLE",
    "oracledb": "ORACLE",

    "db2": "DB2",
    "ibm db2": "DB2",
    "ibmdb2": "DB2",

    "sqlserver": "SQLSERVER",
    "sql server": "SQLSERVER",
    "mssql": "SQLSERVER",
    "sql": "SQLSERVER",
    "microsoft sql": "SQLSERVER",

    "ase": "ASE",
    "sybase": "ASE",
    "sap ase": "ASE",

    "none": "NONE",
    "keine": "NONE",
    "no db": "NONE",
    "no database": "NONE",
}

# OS variations
OS_TYPOS: Dict[str, Tuple[str, str, str]] = {
    # SUSE variations -> (publisher, offer, sku)
    "suse": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "sles": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "suse latest": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "sles latest": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "suse 15": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "sles 15": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "suse 15 sp5": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "sles 15 sp5": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "sles-sap-15-sp5": ("SUSE", "sles-sap-15-sp5", "gen2"),
    "suse 15 sp4": ("SUSE", "sles-sap-15-sp4", "gen2"),
    "sles 15 sp4": ("SUSE", "sles-sap-15-sp4", "gen2"),
    "sles-sap-15-sp4": ("SUSE", "sles-sap-15-sp4", "gen2"),
    "suse 15 sp3": ("SUSE", "sles-sap-15-sp3", "gen2"),
    "sles 15 sp3": ("SUSE", "sles-sap-15-sp3", "gen2"),
    "suse 12": ("SUSE", "sles-sap-12-sp5", "gen2"),
    "sles 12": ("SUSE", "sles-sap-12-sp5", "gen2"),
    "sles 12 sp5": ("SUSE", "sles-sap-12-sp5", "gen2"),

    # Red Hat variations
    "redhat": ("RedHat", "RHEL-SAP-HA", "9_0"),
    "red hat": ("RedHat", "RHEL-SAP-HA", "9_0"),
    "rhel": ("RedHat", "RHEL-SAP-HA", "9_0"),
    "rhel latest": ("RedHat", "RHEL-SAP-HA", "9_0"),
    "rhel 9": ("RedHat", "RHEL-SAP-HA", "9_0"),
    "red hat 9": ("RedHat", "RHEL-SAP-HA", "9_0"),
    "rhel 8": ("RedHat", "RHEL-SAP-HA", "8.6"),
    "red hat 8": ("RedHat", "RHEL-SAP-HA", "8.6"),
    "rhel 8.6": ("RedHat", "RHEL-SAP-HA", "8.6"),
    "rhel 8.4": ("RedHat", "RHEL-SAP-HA", "8.4"),
    "rhel 7": ("RedHat", "RHEL-SAP-HA", "7.9"),
}

# Database sizing variations
SIZING_TYPOS: Dict[str, Tuple[str, str]] = {
    # Demo/Test -> (database_size, purpose)
    "demo": ("Demo", "demo"),
    "test": ("Demo", "testing"),
    "testing": ("Demo", "testing"),
    "sandbox": ("Demo", "demo"),
    "poc": ("Demo", "demo"),
    "proof of concept": ("Demo", "demo"),
    "s4demo": ("S4Demo", "demo"),

    # Development
    "dev": ("E20ds_v4", "development"),
    "development": ("E20ds_v4", "development"),
    "entwicklung": ("E20ds_v4", "development"),

    # Small
    "small": ("E20ds_v4", "development"),
    "klein": ("E20ds_v4", "development"),
    "minimal": ("E20ds_v4", "development"),

    # Medium
    "medium": ("E32ds_v4", "qa"),
    "mittel": ("E32ds_v4", "qa"),
    "qa": ("E32ds_v4", "qa"),
    "staging": ("E32ds_v4", "qa"),

    # Large
    "large": ("E64ds_v5", "production"),
    "gross": ("E64ds_v5", "production"),
    "groß": ("E64ds_v5", "production"),
    "prod": ("E64ds_v5", "production"),
    "production": ("E64ds_v5", "production"),
    "produktiv": ("E64ds_v5", "production"),

    # XLarge
    "xlarge": ("M128s", "production"),
    "xl": ("M128s", "production"),
    "extra large": ("M128s", "production"),
    "very large": ("M128s", "production"),
    "high load": ("M128s", "production"),

    # XXLarge
    "xxlarge": ("M208ms_v2", "production"),
    "xxl": ("M208ms_v2", "production"),
    "huge": ("M208ms_v2", "production"),
    "massive": ("M208ms_v2", "production"),
}


def normalize_region(input_str: str) -> Optional[str]:
    """Normalize Azure region input with typo correction"""
    if not input_str:
        return None

    normalized = input_str.lower().strip().replace("-", "").replace("_", "").replace(" ", "")

    # Check typo map first
    for typo, correct in REGION_TYPOS.items():
        if normalized == typo.replace("-", "").replace("_", "").replace(" ", ""):
            return correct

    # Check if it's already a valid region
    from config import AZURE_REGION_CODES
    for region in AZURE_REGION_CODES.keys():
        if normalized == region.replace("-", "").replace("_", ""):
            return region

    return None


def normalize_environment(input_str: str) -> Optional[str]:
    """Normalize environment input with typo correction"""
    if not input_str:
        return None

    normalized = input_str.lower().strip()

    # Check typo map first
    if normalized in ENVIRONMENT_TYPOS:
        return ENVIRONMENT_TYPOS[normalized]

    # Check uppercase version against valid environments
    from config import VALID_ENVIRONMENTS
    upper = input_str.upper().strip()
    if upper in VALID_ENVIRONMENTS:
        return upper

    return None


def normalize_platform(input_str: str) -> Optional[str]:
    """Normalize database platform input with typo correction"""
    if not input_str:
        return None

    normalized = input_str.lower().strip()

    # Check typo map first
    if normalized in PLATFORM_TYPOS:
        return PLATFORM_TYPOS[normalized]

    # Check uppercase version
    from config import VALID_DB_PLATFORMS
    upper = input_str.upper().strip()
    if upper in VALID_DB_PLATFORMS:
        return upper

    return None


def normalize_os(input_str: str) -> Optional[Dict[str, str]]:
    """Normalize OS selection input and return publisher/offer/sku"""
    if not input_str:
        return None

    normalized = input_str.lower().strip()

    # Check typo map
    for key, (publisher, offer, sku) in OS_TYPOS.items():
        if normalized == key or key in normalized:
            return {
                "publisher": publisher,
                "offer": offer,
                "sku": sku
            }

    return None


def normalize_sizing(input_str: str) -> Optional[Dict[str, str]]:
    """Normalize sizing input and return database_size/purpose"""
    if not input_str:
        return None

    normalized = input_str.lower().strip()

    # Check typo map
    for key, (db_size, purpose) in SIZING_TYPOS.items():
        if key in normalized:
            return {
                "database_size": db_size,
                "purpose": purpose
            }

    return None


def extract_number_selection(input_str: str, max_options: int) -> Optional[int]:
    """Extract number from input like "1", "option 1", "nummer 1", etc."""
    if not input_str:
        return None

    normalized = input_str.lower().strip()

    # Direct number
    if normalized.isdigit():
        num = int(normalized)
        if 1 <= num <= max_options:
            return num

    # "option X", "nummer X", "choice X"
    patterns = [
        r'(?:option|nummer|choice|auswahl|select|wahl)\s*(\d+)',
        r'(\d+)(?:st|nd|rd|th)?(?:\s*option)?',
        r'^(\d+)\s*$',
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            num = int(match.group(1))
            if 1 <= num <= max_options:
                return num

    return None


def clean_input(input_str: str) -> str:
    """Clean up user input - remove extra whitespace, normalize quotes"""
    if not input_str:
        return ""

    # Remove extra whitespace
    cleaned = " ".join(input_str.split())

    # Normalize quotes
    cleaned = cleaned.replace('"', '"').replace('"', '"')
    cleaned = cleaned.replace("'", "'").replace("'", "'")

    return cleaned.strip()
