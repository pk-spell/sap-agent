"""
Config Data Module
==================

Pre-configured data including quick-select templates.
"""

from .quick_templates import (
    QUICK_TEMPLATES,
    find_template_by_input,
    get_templates_menu,
    get_template_summary
)

__all__ = [
    "QUICK_TEMPLATES",
    "find_template_by_input",
    "get_templates_menu",
    "get_template_summary",
]
