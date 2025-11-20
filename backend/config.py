"""
Configuration
=============

Application configuration, constants, and LLM setup.
"""

from pathlib import Path
from langchain_ollama import OllamaLLM

# ============================================================================
# PATHS
# ============================================================================

DB_PATH = Path("/app/data/chat_sessions_v2.db")
TEMPLATES_DIR = Path("/app/templates")
EASY_DEFAULTS_PATH = TEMPLATES_DIR / "easy_defaults.yaml"
TFVARS_TEMPLATE_PATH = TEMPLATES_DIR / "sap.tfvars.j2"

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

llm = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434",
    temperature=0.3  # Lower temperature for more consistent parsing
)

# LLM Timeout Configuration
LLM_TIMEOUT_SECONDS = 15  # Max time to wait for LLM response

# ============================================================================
# VALID VALUES
# ============================================================================

# SDAF-compliant environment codes (max 5 chars, used in naming)
# Based on Microsoft SDAF documentation and best practices
VALID_ENVIRONMENTS = [
    # Production
    "PROD",     # Production
    "PRD",      # Production (short)

    # Non-Production
    "DEV",      # Development
    "QA",       # Quality Assurance
    "QAS",      # Quality Assurance (SAP standard)
    "TST",      # Test
    "TEST",     # Test (longer)
    "UAT",      # User Acceptance Testing
    "SBX",      # Sandbox
    "SBOX",     # Sandbox (longer)
    "LAB",      # Lab

    # Others
    "NP",       # Non-Production (generic)
    "NONPRO",   # Non-Production (5 char limit)
    "DEMO",     # Demo
    "MGMT",     # Management/Control Plane
    "POC",      # Proof of Concept
    "TRAIN",    # Training (5 char limit)
]

VALID_DB_PLATFORMS = [
    "HANA",         # SAP HANA
    "DB2",          # IBM DB2
    "ORACLE",       # Oracle Database
    "ORACLE-ASM",   # Oracle with ASM
    "ASE",          # SAP ASE (Sybase)
    "SQLSERVER",    # Microsoft SQL Server
    "NONE"          # No database tier
]

VALID_OS_TYPES = [
    "LINUX", "WINDOWS"
]

# ============================================================================
# AZURE REGION CODES
# ============================================================================

AZURE_REGION_CODES = {
    # Europe
    "westeurope": "WEEU", "northeurope": "NOEU", "germanywestcentral": "DEWC",
    "francecentral": "FRCE", "uksouth": "UKSO", "switzerlandnorth": "SZNO",
    "norwayeast": "NOEA", "swedencentral": "SECE",

    # Americas
    "eastus": "EAUS", "eastus2": "EUS2", "westus": "WEUS", "westus2": "WUS2",
    "westus3": "WUS3", "centralus": "CEUS", "northcentralus": "NCUS",
    "southcentralus": "SCUS", "canadacentral": "CACE", "canadaeast": "CAEA",
    "brazilsouth": "BRSO",

    # Asia Pacific
    "eastasia": "EAAS", "southeastasia": "SEAS", "australiaeast": "AUEA",
    "australiasoutheast": "AUSE", "japaneast": "JAEA", "japanwest": "JAWE",
    "koreacentral": "KOCE", "koreasouth": "KOSO", "centralindia": "INCE",
    "southindia": "INSO", "westindia": "INWE",

    # Middle East & Africa
    "uaenorth": "UANO", "southafricanorth": "SANO"
}
