"""
Quick-Select Templates
======================

Pre-configured templates for common SAP deployment scenarios.
Users can select these by number or keyword.
"""

from typing import Dict, Any, List

# Quick-select templates for common scenarios
QUICK_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "S/4HANA Development",
        "keywords": ["s4hana dev", "s4 dev", "s/4 dev", "development", "dev template", "template 1", "1"],
        "description": "Standard development environment - single instance, HANA, SUSE, small sizing",
        "config": {
            "environment": "DEV",
            "location": "westeurope",
            "network_logical_name": "SAP01",
            "sid": "D01",
            "database_sid": "HDB",
            "database_platform": "HANA",
            "database_size": "E20ds_v4",
            "purpose": "development",
            "app_tier_sizing_dictionary_key": "Optimized",
            "enable_app_tier_deployment": False,
            "scs_server_count": 0,
            "application_server_count": 0,
            "database_server_count": 1,
            "database_high_availability": False,
            "scs_high_availability": False,
            "architecture_type": "standalone",
            "ha_enabled": False,
            "network_type": "greenfield",
            "admin_subnet": "10.1.0.0/24",
            "db_subnet": "10.1.1.0/24",
            "app_subnet": "10.1.2.0/24",
            "web_subnet": "10.1.3.0/24",
            "os_publisher": "SUSE",
            "os_offer": "sles-sap-15-sp5",
            "os_sku": "gen2",
        }
    },
    {
        "id": 2,
        "name": "S/4HANA QA/Test",
        "keywords": ["s4hana qa", "s4 qa", "qa template", "test template", "template 2", "2"],
        "description": "QA/Test environment - single instance, HANA, SUSE, medium sizing",
        "config": {
            "environment": "QA",
            "location": "westeurope",
            "network_logical_name": "SAP01",
            "sid": "Q01",
            "database_sid": "HDB",
            "database_platform": "HANA",
            "database_size": "E32ds_v4",
            "purpose": "qa",
            "app_tier_sizing_dictionary_key": "Optimized",
            "enable_app_tier_deployment": False,
            "scs_server_count": 0,
            "application_server_count": 0,
            "database_server_count": 1,
            "database_high_availability": False,
            "scs_high_availability": False,
            "architecture_type": "standalone",
            "ha_enabled": False,
            "network_type": "greenfield",
            "admin_subnet": "10.2.0.0/24",
            "db_subnet": "10.2.1.0/24",
            "app_subnet": "10.2.2.0/24",
            "web_subnet": "10.2.3.0/24",
            "os_publisher": "SUSE",
            "os_offer": "sles-sap-15-sp5",
            "os_sku": "gen2",
        }
    },
    {
        "id": 3,
        "name": "S/4HANA Production (Standalone)",
        "keywords": ["s4hana prod", "s4 prod", "production", "prod template", "template 3", "3"],
        "description": "Production environment - single instance, HANA, SUSE, large sizing (no HA)",
        "config": {
            "environment": "PROD",
            "location": "westeurope",
            "network_logical_name": "SAP01",
            "sid": "P01",
            "database_sid": "HDB",
            "database_platform": "HANA",
            "database_size": "E64ds_v5",
            "purpose": "production",
            "app_tier_sizing_dictionary_key": "Optimized",
            "enable_app_tier_deployment": False,
            "scs_server_count": 0,
            "application_server_count": 0,
            "database_server_count": 1,
            "database_high_availability": False,
            "scs_high_availability": False,
            "architecture_type": "standalone",
            "ha_enabled": False,
            "network_type": "greenfield",
            "admin_subnet": "10.3.0.0/24",
            "db_subnet": "10.3.1.0/24",
            "app_subnet": "10.3.2.0/24",
            "web_subnet": "10.3.3.0/24",
            "os_publisher": "SUSE",
            "os_offer": "sles-sap-15-sp5",
            "os_sku": "gen2",
        }
    },
    {
        "id": 4,
        "name": "Demo/Sandbox",
        "keywords": ["demo", "sandbox", "poc", "proof of concept", "template 4", "4"],
        "description": "Demo/Sandbox - minimal resources, HANA, cost-optimized",
        "config": {
            "environment": "SBX",
            "location": "westeurope",
            "network_logical_name": "SAP01",
            "sid": "SBX",
            "database_sid": "HDB",
            "database_platform": "HANA",
            "database_size": "Demo",
            "purpose": "demo",
            "app_tier_sizing_dictionary_key": "Optimized",
            "enable_app_tier_deployment": False,
            "scs_server_count": 0,
            "application_server_count": 0,
            "database_server_count": 1,
            "database_high_availability": False,
            "scs_high_availability": False,
            "architecture_type": "standalone",
            "ha_enabled": False,
            "network_type": "greenfield",
            "admin_subnet": "10.0.0.0/24",
            "db_subnet": "10.0.1.0/24",
            "app_subnet": "10.0.2.0/24",
            "web_subnet": "10.0.3.0/24",
            "os_publisher": "SUSE",
            "os_offer": "sles-sap-15-sp5",
            "os_sku": "gen2",
        }
    },
]


def find_template_by_input(user_input: str) -> Dict[str, Any] | None:
    """Find a template by user input (number or keyword)"""
    if not user_input:
        return None

    normalized = user_input.lower().strip()

    # FIRST: Check for exact number match (highest priority)
    if normalized.isdigit():
        num = int(normalized)
        for template in QUICK_TEMPLATES:
            if template["id"] == num:
                return template
        return None  # No template with that ID

    # SECOND: Check for exact keyword match
    for template in QUICK_TEMPLATES:
        for keyword in template["keywords"]:
            # Exact match only (not substring)
            if keyword == normalized:
                return template

    # THIRD: Check if input contains a keyword or keyword contains input
    # But only for longer inputs (3+ chars) to avoid false matches
    if len(normalized) >= 3:
        for template in QUICK_TEMPLATES:
            for keyword in template["keywords"]:
                # Skip short keywords to avoid false matches
                if len(keyword) < 3:
                    continue
                if keyword in normalized or normalized in keyword:
                    return template

            # Check by name
            if normalized in template["name"].lower():
                return template

    return None


def get_templates_menu() -> str:
    """Generate a menu string showing all available templates"""
    menu = """**Quick Templates** (type the number or name):

"""
    for template in QUICK_TEMPLATES:
        menu += f"**[{template['id']}]** {template['name']}\n"
        menu += f"    _{template['description']}_\n\n"

    return menu


def get_template_summary(template: Dict[str, Any]) -> str:
    """Generate a summary of a selected template"""
    config = template["config"]
    return f"""**Selected Template: {template['name']}**

| Setting | Value |
|---------|-------|
| Environment | {config['environment']} |
| Region | {config['location']} |
| Network | {config['network_logical_name']} |
| SAP SID | {config['sid']} |
| Database | {config['database_platform']} ({config['database_sid']}) |
| Sizing | {config['database_size']} |
| OS | {config['os_publisher']} {config['os_offer']} |
| Architecture | {config['architecture_type'].capitalize()} |

You can customize any value or confirm to generate the tfvars file."""
