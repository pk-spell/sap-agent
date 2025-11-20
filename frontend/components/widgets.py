"""
Interactive Widgets for SAP Deployment Configuration
=====================================================

Form-based widgets for structured input collection.
"""

import streamlit as st
from typing import Optional


def render_environment_form() -> Optional[str]:
    """
    Render interactive form for Prompt 0 (Environment selection)

    Returns:
        Optional[str]: Formatted message to send to backend, or None if not submitted
    """
    st.markdown("### 🌍 Environment Configuration")
    st.markdown("Please provide the following information:")

    with st.form(key="environment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            environment = st.selectbox(
                "Environment Type",
                options=["DEV", "PROD", "QA", "UAT", "TEST", "NONPROD", "SANDBOX"],
                index=0,
                help="Select the environment type for your SAP deployment"
            )

            location = st.selectbox(
                "Azure Region",
                options=[
                    "westeurope", "northeurope", "germanywestcentral",
                    "eastus", "eastus2", "westus", "westus2", "centralus",
                    "uksouth", "francecentral", "switzerlandnorth", "norwayeast"
                ],
                index=0,
                help="Select the Azure region where you want to deploy"
            )

        with col2:
            network_name = st.text_input(
                "Network Name",
                value="SAP01",
                max_chars=7,
                help="Short identifier for your network (max 7 characters)"
            )

            st.markdown("---")
            submit_button = st.form_submit_button("✅ Continue", use_container_width=True, type="primary")

        if submit_button:
            # Validate network name
            if not network_name or len(network_name) > 7:
                st.error("Network name must be 1-7 characters")
                return None

            # Format message for backend
            message = f"{environment}, {location}, {network_name}"
            return message

    return None


def render_sap_system_form() -> Optional[str]:
    """
    Render interactive form for Prompt 1 (SAP System identity)

    Returns:
        Optional[str]: Formatted message to send to backend, or None if not submitted
    """
    st.markdown("### 💾 SAP System Identification")
    st.markdown("Please identify your SAP system:")

    with st.form(key="sap_system_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            sap_sid = st.text_input(
                "SAP Application SID",
                value="X00",
                max_chars=3,
                help="3-character SAP Application SID (e.g., X00, P01, S15)"
            ).upper()

            db_sid = st.text_input(
                "Database SID",
                value="HDB",
                max_chars=3,
                help="3-character Database SID (e.g., HDB, XDB, ORA)"
            ).upper()

        with col2:
            db_platform = st.selectbox(
                "Database Platform",
                options=["HANA", "DB2", "ORACLE", "ASE", "SQLSERVER", "NONE"],
                index=0,
                help="Select the database platform for your SAP system"
            )

            st.markdown("---")
            submit_button = st.form_submit_button("✅ Continue", use_container_width=True, type="primary")

        if submit_button:
            # Validate SIDs
            if not sap_sid or len(sap_sid) != 3:
                st.error("SAP SID must be exactly 3 characters")
                return None
            if not db_sid or len(db_sid) != 3:
                st.error("Database SID must be exactly 3 characters")
                return None

            # Format message for backend
            message = f"{sap_sid}, {db_sid}, {db_platform}"
            return message

    return None
