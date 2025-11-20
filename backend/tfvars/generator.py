"""
TFVARS Generator
================

Generate SDAF-compliant Terraform variable files from user configuration.
"""

import logging
import yaml
from datetime import datetime
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from config import TEMPLATES_DIR, EASY_DEFAULTS_PATH, TFVARS_TEMPLATE_PATH

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def load_defaults() -> Dict[str, Any]:
    """Load default values from easy_defaults.yaml"""
    try:
        with open(EASY_DEFAULTS_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load defaults: {e}")
        return {}


def generate_tfvars(user_data: Dict[str, Any]) -> str:
    """Generate SDAF-compliant tfvars file from collected user data"""
    try:
        # Load defaults
        config = load_defaults()

        # Update with user-collected data
        # Prompt 0: Environment
        if "environment" in user_data:
            config["environment"] = user_data["environment"]
        if "location" in user_data:
            config["location"] = user_data["location"]
        if "network_logical_name" in user_data:
            config["network_logical_name"] = user_data["network_logical_name"]

        # Prompt 1: SAP System
        if "sid" in user_data:
            config["sid"] = user_data["sid"]
            config["sap_sid"] = user_data["sid"]
            config["sap_system_name"] = user_data["sid"]
        if "database_sid" in user_data:
            config["database_sid"] = user_data["database_sid"]
        if "database_platform" in user_data:
            config["database_platform"] = user_data["database_platform"]

        # Prompt 2: Sizing
        if "database_size" in user_data:
            config["database_size"] = user_data["database_size"]
        if "app_tier_sizing_dictionary_key" in user_data:
            config["app_tier_sizing_dictionary_key"] = user_data["app_tier_sizing_dictionary_key"]

        # Prompt 3: Architecture
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

        # Prompt 4: Network
        if user_data.get("network_type") == "greenfield":
            config["admin_subnet_address_prefix"] = user_data.get("admin_subnet", "10.1.0.0/24")
            config["db_subnet_address_prefix"] = user_data.get("db_subnet", "10.1.1.0/24")
            config["app_subnet_address_prefix"] = user_data.get("app_subnet", "10.1.2.0/24")
            config["web_subnet_address_prefix"] = user_data.get("web_subnet", "10.1.3.0/24")

        # Prompt 5: OS
        if "os_publisher" in user_data:
            vm_image = {
                "os_type": "LINUX",
                "publisher": user_data["os_publisher"],
                "offer": user_data["os_offer"],
                "sku": user_data["os_sku"],
                "version": "latest",
                "type": "marketplace"
            }
            config["database_vm_image"] = vm_image
            config["scs_server_image"] = vm_image
            config["application_server_image"] = vm_image
            config["webdispatcher_server_image"] = vm_image

        # Add metadata
        config["_generated_by"] = "SDAF Chat Agent v2"
        config["_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Render template
        template = jinja_env.get_template("sap.tfvars.j2")
        return template.render(config=config)

    except Exception as e:
        logger.error(f"Failed to generate tfvars: {e}")
        return f"# Error generating tfvars: {str(e)}"
