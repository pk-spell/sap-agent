"""
TFVARS Generator Module
=======================

Generate SDAF-compliant tfvars files from collected user data.
"""

from .generator import generate_tfvars

__all__ = ["generate_tfvars"]
