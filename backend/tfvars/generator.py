"""
TFVARS Generator
================

Generate SDAF-compliant Terraform variable files from user configuration.
Based on official SDAF examples from Azure/sap-automation-samples.
"""

import logging
import yaml
from datetime import datetime
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from config import TEMPLATES_DIR, EASY_DEFAULTS_PATH

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Database size mapping: user-friendly names to VM SKUs
DATABASE_SIZE_MAP = {
    # Demo/Dev sizes
    "demo": "E20ds_v4",
    "s4demo": "E20ds_v4",
    "development": "E20ds_v4",
    "dev": "E20ds_v4",

    # Small sizes (160-256 GB)
    "small": "E20ds_v4",
    "e20ds_v4": "E20ds_v4",
    "e20ds": "E20ds_v4",

    # Medium sizes (256-512 GB)
    "medium": "E32ds_v4",
    "e32ds_v4": "E32ds_v4",
    "e32ds": "E32ds_v4",
    "e64ds_v4": "E64ds_v4",
    "e64ds": "E64ds_v4",

    # Large sizes (512 GB - 1 TB)
    "large": "E64ds_v5",
    "e64ds_v5": "E64ds_v5",
    "m64ls": "M64ls",
    "m64s": "M64s",

    # XLarge sizes (1-4 TB)
    "xlarge": "M128s",
    "m128s": "M128s",
    "m128ms": "M128ms",

    # XXLarge sizes (4+ TB)
    "xxlarge": "M208ms_v2",
    "m208ms_v2": "M208ms_v2",
}


def load_defaults() -> Dict[str, Any]:
    """Load default values from easy_defaults.yaml"""
    try:
        with open(EASY_DEFAULTS_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load defaults: {e}")
        return {}


def map_database_size(size_input: str) -> str:
    """Map user-friendly database size to VM SKU"""
    if not size_input:
        return "E20ds_v4"

    size_lower = size_input.lower().strip()

    # Direct SKU match
    if size_lower in DATABASE_SIZE_MAP:
        return DATABASE_SIZE_MAP[size_lower]

    # Partial match
    for key, sku in DATABASE_SIZE_MAP.items():
        if key in size_lower:
            return sku

    # If it looks like a SKU already (starts with E, M, or Standard_)
    if size_input.startswith(('E', 'M', 'Standard_')):
        return size_input

    # Default
    return "E20ds_v4"


def generate_tfvars(user_data: Dict[str, Any]) -> str:
    """Generate SDAF-compliant tfvars file from collected user data"""
    try:
        # Load defaults
        config = load_defaults()

        # =====================================================================
        # Environment/Application (Prompt 0)
        # =====================================================================
        if "environment" in user_data:
            config["environment"] = user_data["environment"].upper()
        if "location" in user_data:
            config["location"] = user_data["location"].lower()
        if "network_logical_name" in user_data:
            config["network_logical_name"] = user_data["network_logical_name"].upper()

        # =====================================================================
        # SAP System Identity (Prompt 1)
        # =====================================================================
        if "sid" in user_data:
            config["sid"] = user_data["sid"].upper()
        if "database_sid" in user_data:
            config["database_sid"] = user_data["database_sid"].upper()
        if "database_platform" in user_data:
            config["database_platform"] = user_data["database_platform"].upper()

        # Generate description
        config["description"] = f"{config.get('database_platform', 'SAP')} system on {config.get('os_offer', 'Linux')}"

        # =====================================================================
        # Sizing (Prompt 2)
        # =====================================================================
        if "database_size" in user_data:
            size_input = user_data["database_size"]
            config["database_size"] = map_database_size(size_input)

        if "app_tier_sizing_dictionary_key" in user_data:
            config["app_tier_sizing_dictionary_key"] = user_data["app_tier_sizing_dictionary_key"]

        # =====================================================================
        # Architecture (Prompt 3)
        # =====================================================================
        if "enable_app_tier_deployment" in user_data:
            config["enable_app_tier_deployment"] = user_data["enable_app_tier_deployment"]
        if "application_server_count" in user_data:
            config["application_server_count"] = user_data["application_server_count"]
        if "scs_server_count" in user_data:
            config["scs_server_count"] = user_data["scs_server_count"]
        if "database_server_count" in user_data:
            config["database_server_count"] = user_data["database_server_count"]
        if "database_high_availability" in user_data:
            config["database_high_availability"] = user_data["database_high_availability"]
        if "scs_high_availability" in user_data:
            config["scs_high_availability"] = user_data["scs_high_availability"]
        if "webdispatcher_server_count" in user_data:
            config["webdispatcher_server_count"] = user_data["webdispatcher_server_count"]

        # Set deployment type based on architecture
        if config.get("enable_app_tier_deployment") == False and config.get("scs_server_count", 0) == 0:
            config["deployment_type"] = "Single Instance (Standard)"
        elif config.get("database_high_availability") or config.get("scs_high_availability"):
            config["deployment_type"] = "High Availability"
        else:
            config["deployment_type"] = "Distributed"

        # =====================================================================
        # Network (Prompt 4)
        # =====================================================================
        if "network_type" in user_data:
            config["network_type"] = user_data["network_type"].lower()

        # Greenfield subnet configuration
        if config.get("network_type") == "greenfield":
            if "admin_subnet" in user_data:
                config["admin_subnet"] = user_data["admin_subnet"]
            if "db_subnet" in user_data:
                config["db_subnet"] = user_data["db_subnet"]
            if "app_subnet" in user_data:
                config["app_subnet"] = user_data["app_subnet"]
            if "web_subnet" in user_data:
                config["web_subnet"] = user_data["web_subnet"]

        # Brownfield subnet ARMs
        elif config.get("network_type") == "brownfield":
            if "admin_subnet_arm_id" in user_data:
                config["admin_subnet_arm_id"] = user_data["admin_subnet_arm_id"]
            if "db_subnet_arm_id" in user_data:
                config["db_subnet_arm_id"] = user_data["db_subnet_arm_id"]
            if "app_subnet_arm_id" in user_data:
                config["app_subnet_arm_id"] = user_data["app_subnet_arm_id"]
            if "web_subnet_arm_id" in user_data:
                config["web_subnet_arm_id"] = user_data["web_subnet_arm_id"]

        # =====================================================================
        # Operating System (Prompt 5)
        # =====================================================================
        if "os_publisher" in user_data:
            config["os_publisher"] = user_data["os_publisher"]
        if "os_offer" in user_data:
            config["os_offer"] = user_data["os_offer"]
        if "os_sku" in user_data:
            config["os_sku"] = user_data["os_sku"]
        if "os_type" in user_data:
            config["os_type"] = user_data["os_type"]

        # Update description with OS info
        config["description"] = f"{config.get('database_platform', 'SAP')} system on {config.get('os_publisher', 'SUSE')} {config.get('os_offer', 'sles-sap-15-sp5')}"

        # =====================================================================
        # Add metadata
        # =====================================================================
        config["_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config["_generated_by"] = "SDAF Assistant"

        # =====================================================================
        # Render template
        # =====================================================================
        template = jinja_env.get_template("sap_system.tfvars.j2")
        return template.render(config=config)

    except Exception as e:
        logger.error(f"Failed to generate tfvars: {e}")
        return f"# Error generating tfvars: {str(e)}"


def generate_tfvars_preview(user_data: Dict[str, Any]) -> str:
    """Generate a preview of the tfvars file (same as generate_tfvars but can be extended)"""
    return generate_tfvars(user_data)
