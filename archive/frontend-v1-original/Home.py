"""
SAP Deployment Assistant - Landing Page
=========================================

Beautiful landing page for the SDAF Chat Agent
"""

import streamlit as st
import os

# Page config
st.set_page_config(
    page_title="SAP Deployment Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Elex Clerics Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');

    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #151b2d;
        --bg-tertiary: #1e2842;
        --accent-cyan: #00d9ff;
        --accent-blue: #0066ff;
        --text-primary: #e0e6ed;
        --text-secondary: #8a95a8;
        --border: #2a3f5f;
    }

    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f1420 50%, #0a0e1a 100%);
        font-family: 'Rajdhani', sans-serif;
        color: var(--text-primary);
    }

    h1 {
        font-family: 'Orbitron', monospace !important;
        color: var(--accent-cyan) !important;
        text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
        font-weight: 900 !important;
        letter-spacing: 3px;
        text-align: center;
        font-size: 3.5rem !important;
        margin-bottom: 1rem;
    }

    h2, h3 {
        font-family: 'Orbitron', monospace !important;
        color: var(--accent-cyan) !important;
        text-align: center;
    }

    p, li {
        color: var(--text-primary);
        font-size: 1.1rem;
        line-height: 1.8;
    }

    .hero-box {
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
        border: 2px solid var(--border);
        border-radius: 12px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 900px;
        box-shadow: 0 8px 30px rgba(0, 217, 255, 0.15);
        text-align: center;
    }

    .feature-card {
        background: var(--bg-tertiary);
        border-left: 4px solid var(--accent-cyan);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    .feature-card h3 {
        color: var(--accent-cyan);
        margin-bottom: 0.5rem;
        text-align: left !important;
    }

    .feature-card p {
        color: var(--text-secondary);
        font-size: 1rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%);
        border: none;
        color: var(--bg-primary);
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        font-size: 1.3rem;
        padding: 1rem 3rem;
        border-radius: 8px;
        box-shadow: 0 6px 25px rgba(0, 217, 255, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .stButton > button:hover {
        box-shadow: 0 8px 35px rgba(0, 217, 255, 0.7);
        transform: translateY(-3px) scale(1.05);
    }

    .tech-badge {
        display: inline-block;
        background: rgba(0, 217, 255, 0.1);
        border: 1px solid var(--accent-cyan);
        color: var(--accent-cyan);
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-size: 0.85rem;
        margin: 0.2rem;
        font-family: 'Orbitron', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("<div class='hero-box'>", unsafe_allow_html=True)
st.title("🤖 SAP DEPLOYMENT ASSISTANT")
st.markdown("""
<h3 style='color: var(--text-secondary); font-family: Rajdhani; font-weight: 400; margin-top: 0;'>
Automated SDAF Configuration Generator
</h3>
""", unsafe_allow_html=True)

st.markdown("""
<p style='font-size: 1.2rem; color: var(--text-primary); margin: 2rem 0;'>
Generate production-ready Terraform variable files for SAP deployments on Azure<br/>
using natural language conversations powered by AI.
</p>
""", unsafe_allow_html=True)

# CTA Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 TRY NOW", use_container_width=True):
        st.switch_page("pages/chat.py")

st.markdown("</div>", unsafe_allow_html=True)

# Features Section
st.markdown("<h2 style='margin-top: 3rem;'>✨ FEATURES</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='feature-card'>
        <h3>⚡ Conversational Interface</h3>
        <p>Simply describe your SAP deployment in plain language - no complex configuration files needed.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='feature-card'>
        <h3>🎯 Intelligent Defaults</h3>
        <p>180+ pre-configured SDAF parameters with best-practice defaults. You only specify what matters.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='feature-card'>
        <h3>📊 46 Sizing Options</h3>
        <p>From demo systems to production workloads with up to 4TB+ memory configurations.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='feature-card'>
        <h3>🔄 Session Management</h3>
        <p>Save, switch, and resume multiple configuration sessions with persistent history.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='feature-card'>
        <h3>✅ SDAF Compliant</h3>
        <p>Generates validated tfvars files ready for SAP Deployment Automation Framework.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='feature-card'>
        <h3>🚀 Fast & Responsive</h3>
        <p>Hybrid parsing with regex fallbacks for instant responses on common patterns.</p>
    </div>
    """, unsafe_allow_html=True)

# Tech Stack
st.markdown("<h2 style='margin-top: 3rem;'>🛠 POWERED BY</h2>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin: 2rem 0;'>
    <span class='tech-badge'>FastAPI</span>
    <span class='tech-badge'>LangChain</span>
    <span class='tech-badge'>Ollama</span>
    <span class='tech-badge'>Streamlit</span>
    <span class='tech-badge'>SQLite</span>
    <span class='tech-badge'>SDAF</span>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<p style='text-align: center; color: var(--text-secondary); font-size: 0.9rem; margin-top: 2rem;'>
SAP Deployment Assistant v2.0 | Built with Claude Code
</p>
""", unsafe_allow_html=True)
