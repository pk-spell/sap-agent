import streamlit as st
import requests
import json

st.set_page_config(page_title="SDAF Generator", layout="wide")
st.title("SAP Deployment Automation Framework - Config Generator")

API_URL = "http://backend:8000"

# Session State
if "config" not in st.session_state:
    st.session_state.config = {}
if "phase" not in st.session_state:
    st.session_state.phase = 1

# Health Check
try:
    health = requests.get(f"{API_URL}/health", timeout=2).json()
    st.sidebar.success("✓ Backend erreichbar")
except:
    st.sidebar.error("✗ Backend nicht erreichbar")

# Phasen
if st.session_state.phase == 1:
    st.subheader("Phase 1: Umgebung")
    st.session_state.config["deployer_env"] = st.selectbox("Deployer", ["MGMT","DEV","TST","PRD"])
    st.session_state.config["workload_env"] = st.selectbox("Workload", ["DEV","TST","PRD"])
    if st.button("Weiter"):
        st.session_state.phase = 2
        st.rerun()

elif st.session_state.phase == 2:
    st.subheader("Phase 2: SAP System")
    sid = st.text_input("SAP SID (3 Zeichen)", "X01")
    if st.button("Validieren"):
        resp = requests.post(f"{API_URL}/validate", json={"field": "sap_sid", "value": sid}).json()
        if resp["valid"]:
            st.success(resp["message"])
            st.session_state.config["sap_sid"] = sid
        else:
            st.error(resp["message"])
    
    if "sap_sid" in st.session_state.config and st.button("Weiter"):
        st.session_state.config["sap_product"] = st.selectbox("Produkt", ["S4HANA2023", "S4HANA2022", "SAP_NETWEAVER_750"])
        st.session_state.phase = 3
        st.rerun()

elif st.session_state.phase == 3:
    st.subheader("Phase 3: Generierung")
    if st.button("🚀 TFVARS generieren"):
        with st.spinner("Generiere..."):
            resp = requests.post(f"{API_URL}/generate", json={"config": st.session_state.config})
            if resp.status_code == 200:
                tfvars = resp.json()["tfvars"]
                st.download_button("📥 Download", tfvars, f"{st.session_state.config['sap_sid']}.tfvars", "text/plain")
                st.code(tfvars)
            else:
                st.error(resp.json()["detail"])

st.sidebar.json(st.session_state.config)
