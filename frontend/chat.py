# frontend/chat.py - Completely Redesigned with Interactive UX
import streamlit as st
import requests
import uuid
import os
import logging
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="SAP SDAF Configuration Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = os.getenv("API_URL", "http://backend:8000")

# ===========================
# SESSION STATE INITIALIZATION
# ===========================
def init_session_state():
    """Initialize all session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_block" not in st.session_state:
        st.session_state.current_block = "environment"
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "tfvars_ready" not in st.session_state:
        st.session_state.tfvars_ready = False
    if "tfvars_content" not in st.session_state:
        st.session_state.tfvars_content = ""
    if "backend_ready" not in st.session_state:
        st.session_state.backend_ready = False
    if "greeting_shown" not in st.session_state:
        st.session_state.greeting_shown = False
    if "last_saved" not in st.session_state:
        st.session_state.last_saved = None

init_session_state()

# ===========================
# HELPER FUNCTIONS
# ===========================
def check_backend():
    """Check if backend is reachable"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.ok:
            st.session_state.backend_ready = True
            return True
    except Exception:
        st.session_state.backend_ready = False
    return False

def send_message_to_backend(message: str):
    """Send message to backend and get response"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def auto_save_session():
    """Auto-save current session to database"""
    try:
        response = requests.post(
            f"{API_URL}/save-chat",
            json={"session_id": st.session_state.session_id},
            timeout=5
        )
        if response.ok:
            st.session_state.last_saved = datetime.now()
            return True
    except Exception as e:
        logging.error(f"Auto-save failed: {e}")
    return False

def load_chat_history():
    """Load all chat sessions from database"""
    try:
        response = requests.get(f"{API_URL}/list-sessions", timeout=5)
        if response.ok:
            return response.json().get("sessions", [])
    except Exception:
        pass
    return []

def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        response = requests.delete(f"{API_URL}/delete-session/{session_id}", timeout=5)
        return response.ok
    except Exception:
        return False

def load_session(session_id: str):
    """Load a specific session"""
    try:
        response = requests.post(
            f"{API_URL}/load-chat",
            json={"session_id": session_id},
            timeout=5
        )
        if response.ok:
            data = response.json()
            if data.get("found"):
                return data
    except Exception:
        pass
    return None

def reset_chat():
    """Reset to new chat"""
    try:
        requests.post(f"{API_URL}/reset", timeout=5)
    except Exception:
        pass

    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.messages = []
    st.session_state.current_block = "environment"
    st.session_state.user_answers = {}
    st.session_state.tfvars_ready = False
    st.session_state.tfvars_content = ""
    st.session_state.greeting_shown = False
    st.session_state.last_saved = None

def show_greeting():
    """Show initial greeting message"""
    greeting = """Welcome to the SAP SDAF Configuration Assistant!

I help you generate Terraform variable files for SAP deployments on Azure using the SAP Deployment Automation Framework (SDAF).

**What I need from you:**

**Step 1 - Environment Configuration:**
- Deployer Environment (e.g., MGMT)
- Workload Environment (e.g., DEV, TST, PRD)
- Azure Region (e.g., westeurope)

**Step 2 - SAP System Configuration:**
- SAP System ID (SID) - 3 characters (e.g., X01)
- SAP Product (e.g., S4HANA2023)
- System Sizing (small, medium, large)

You can use the interactive buttons below or type your values manually. Let's get started!"""

    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.greeting_shown = True

# ===========================
# SIDEBAR - CHAT HISTORY
# ===========================
with st.sidebar:
    st.title("🗂️ Chat History")

    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        reset_chat()
        st.rerun()

    st.divider()

    # Backend Status
    if check_backend():
        st.success("✅ Backend Connected", icon="🔌")
    else:
        st.error("❌ Backend Offline", icon="🔌")
        if st.button("🔄 Retry Connection"):
            st.rerun()
        st.stop()

    st.divider()

    # Current Session Info
    st.caption("**Current Session**")
    st.code(st.session_state.session_id, language=None)
    if st.session_state.last_saved:
        st.caption(f"Last saved: {st.session_state.last_saved.strftime('%H:%M:%S')}")

    st.divider()

    # Load Chat History
    st.subheader("Previous Chats")
    sessions = load_chat_history()

    if sessions:
        for session in sessions:
            session_id = session["session_id"]
            title = session.get("title", "New Chat")
            updated_at = session.get("updated_at", "")

            # Parse timestamp
            try:
                dt = datetime.fromisoformat(updated_at.replace(' ', 'T'))
                time_str = dt.strftime("%m/%d %H:%M")
            except:
                time_str = "Unknown"

            # Create columns for load and delete buttons
            col1, col2 = st.columns([4, 1])

            with col1:
                # Highlight current session
                is_current = session_id == st.session_state.session_id
                button_type = "primary" if is_current else "secondary"

                if st.button(
                    f"{'📂' if is_current else '📄'} {title}",
                    key=f"load_{session_id}",
                    use_container_width=True,
                    type=button_type,
                    help=f"Updated: {time_str}"
                ):
                    data = load_session(session_id)
                    if data:
                        st.session_state.session_id = session_id
                        st.session_state.messages = data.get("messages", [])
                        st.session_state.user_answers = data.get("user_answers", {})
                        st.session_state.current_block = data.get("current_block", "environment")
                        st.session_state.tfvars_ready = data.get("tfvars_ready", False)
                        st.session_state.greeting_shown = len(st.session_state.messages) > 0
                        st.success(f"Loaded: {title}")
                        st.rerun()

            with col2:
                if st.button("🗑️", key=f"del_{session_id}", help="Delete this chat"):
                    if delete_chat_session(session_id):
                        st.success("Deleted!")
                        if session_id == st.session_state.session_id:
                            reset_chat()
                        st.rerun()
                    else:
                        st.error("Failed to delete")

            st.caption(f"🕒 {time_str}")
            st.divider()
    else:
        st.info("No previous chats yet.\nStart a new conversation!")

    # Manual Save Button
    st.divider()
    if st.button("💾 Save Current Chat", use_container_width=True):
        if auto_save_session():
            st.success("Saved!")
            st.rerun()
        else:
            st.error("Save failed")

# ===========================
# MAIN AREA - CHAT INTERFACE
# ===========================
st.title("🤖 SAP SDAF Configuration Assistant")

# Show greeting if new chat
if not st.session_state.greeting_shown and len(st.session_state.messages) == 0:
    show_greeting()

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===========================
# INTERACTIVE INPUT SECTION
# ===========================
st.divider()

# Show current step indicator
if st.session_state.current_block == "environment":
    st.info("📍 **Step 1/2:** Environment Configuration", icon="🎯")
elif st.session_state.current_block == "sap_system":
    st.info("📍 **Step 2/2:** SAP System Configuration", icon="🎯")
elif st.session_state.current_block == "complete":
    st.success("✅ Configuration Complete!", icon="🎉")

# Interactive Input Based on Current Block
if st.session_state.current_block == "environment":
    st.subheader("Step 1: Environment Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**Deployer Environment**")
        deployer_options = ["MGMT", "DEV", "TST", "PRD"]
        deployer = st.selectbox(
            "Select Deployer",
            deployer_options,
            key="deployer_select",
            label_visibility="collapsed"
        )

    with col2:
        st.caption("**Workload Environment**")
        workload_options = ["DEV", "TST", "QA", "PRD"]
        workload = st.selectbox(
            "Select Workload",
            workload_options,
            key="workload_select",
            label_visibility="collapsed"
        )

    with col3:
        st.caption("**Azure Region**")
        region_options = ["westeurope", "northeurope", "germanywestcentral", "eastus", "westus2"]
        region = st.selectbox(
            "Select Region",
            region_options,
            key="region_select",
            label_visibility="collapsed"
        )

    st.caption("💡 *Or type manually: `MGMT, DEV, westeurope`*")

    if st.button("✅ Submit Environment", use_container_width=True, type="primary"):
        message = f"{deployer}, {workload}, {region}"
        st.session_state.messages.append({"role": "user", "content": message})

        with st.spinner("Processing..."):
            result = send_message_to_backend(message)
            if result:
                st.session_state.messages.append({"role": "assistant", "content": result["reply"]})
                st.session_state.current_block = result["state"]["current_block"]
                st.session_state.user_answers = result["state"]["user_answers"]
                auto_save_session()
                st.rerun()

elif st.session_state.current_block == "sap_system":
    st.subheader("Step 2: SAP System Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**SAP System ID (SID)**")
        sid = st.text_input(
            "3 characters (e.g., X01, P01)",
            max_chars=3,
            key="sid_input",
            label_visibility="collapsed",
            placeholder="X01"
        ).upper()

    with col2:
        st.caption("**SAP Product**")
        product_options = ["S4HANA2023", "S4HANA2022", "S4HANA2021", "SAP_NETWEAVER_750"]
        product = st.selectbox(
            "Select Product",
            product_options,
            key="product_select",
            label_visibility="collapsed"
        )

    with col3:
        st.caption("**System Sizing**")
        sizing_options = {
            "Small (Dev/Test)": "small",
            "Medium (QA/Pre-Prod)": "medium",
            "Large (Production)": "large"
        }
        sizing_display = st.selectbox(
            "Select Sizing",
            list(sizing_options.keys()),
            key="sizing_select",
            label_visibility="collapsed"
        )
        sizing = sizing_options[sizing_display]

    st.caption("💡 *Or type manually: `X01, S4HANA2023, small`*")

    # Show sizing details
    with st.expander("📊 View Sizing Details"):
        if sizing == "small":
            st.markdown("""
            **Small (Development/Testing):**
            - App Server: Standard_D4s_v3 (4 vCPUs, 16 GB RAM)
            - Database: Standard_E16s_v3 (16 vCPUs, 128 GB RAM)
            - SCS: Standard_D2s_v3 (2 vCPUs, 8 GB RAM)
            """)
        elif sizing == "medium":
            st.markdown("""
            **Medium (QA/Pre-Production):**
            - App Server: Standard_D8s_v3 (8 vCPUs, 32 GB RAM)
            - Database: Standard_E32s_v3 (32 vCPUs, 256 GB RAM)
            - SCS: Standard_D4s_v3 (4 vCPUs, 16 GB RAM)
            """)
        else:
            st.markdown("""
            **Large (Production):**
            - App Server: Standard_D16s_v3 (16 vCPUs, 64 GB RAM)
            - Database: Standard_E64s_v3 (64 vCPUs, 432 GB RAM)
            - SCS: Standard_D8s_v3 (8 vCPUs, 32 GB RAM)
            """)

    if st.button("✅ Submit SAP System", use_container_width=True, type="primary"):
        if len(sid) != 3:
            st.error("SID must be exactly 3 characters!")
        else:
            message = f"{sid}, {product}, {sizing}"
            st.session_state.messages.append({"role": "user", "content": message})

            with st.spinner("Generating TFVARS..."):
                result = send_message_to_backend(message)
                if result:
                    st.session_state.messages.append({"role": "assistant", "content": result["reply"]})
                    st.session_state.current_block = result["state"]["current_block"]
                    st.session_state.user_answers = result["state"]["user_answers"]
                    st.session_state.tfvars_ready = result.get("tfvars_ready", False)
                    st.session_state.tfvars_content = result.get("tfvars", "")
                    auto_save_session()
                    st.rerun()

# ===========================
# MANUAL TEXT INPUT (FALLBACK)
# ===========================
st.divider()
st.caption("**Alternative: Manual Text Input**")

if prompt := st.chat_input("Type your message or ask questions...", key="manual_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        result = send_message_to_backend(prompt)
        if result:
            st.session_state.messages.append({"role": "assistant", "content": result["reply"]})

            # Update state
            if "state" in result:
                st.session_state.current_block = result["state"].get("current_block", st.session_state.current_block)
                st.session_state.user_answers = result["state"].get("user_answers", {})
                st.session_state.tfvars_ready = result.get("tfvars_ready", False)
                st.session_state.tfvars_content = result.get("tfvars", "")

            auto_save_session()
            st.rerun()

# ===========================
# DOWNLOAD SECTION
# ===========================
if st.session_state.tfvars_ready and st.session_state.tfvars_content:
    st.divider()
    st.success("🎉 **Configuration Complete!** Your TFVARS file is ready.")

    # Extract SID for filename
    sid = st.session_state.user_answers.get("sap_sid", "config")
    filename = f"{sid}.tfvars"

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.download_button(
            label="📥 Download TFVARS File",
            data=st.session_state.tfvars_content,
            file_name=filename,
            mime="text/plain",
            use_container_width=True,
            type="primary"
        )

    with col2:
        if st.button("🔄 Start New Configuration", use_container_width=True):
            reset_chat()
            st.rerun()

    with col3:
        if st.button("💾 Save", use_container_width=True):
            if auto_save_session():
                st.success("Saved!")

    # Preview
    with st.expander("📄 Preview TFVARS Content"):
        st.code(st.session_state.tfvars_content, language="hcl")

    # Summary
    with st.expander("📋 Configuration Summary"):
        st.json(st.session_state.user_answers)

# ===========================
# FOOTER
# ===========================
st.divider()
st.caption("💡 **Need help?** Type `help` or `What can you do?` in the chat.")
st.caption(f"Session ID: {st.session_state.session_id} | Current Step: {st.session_state.current_block}")
