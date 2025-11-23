# SAP SDAF Configuration Assistant - User Guide

## Quick Start

### Starting a New Configuration

1. **Open the application** - The app will automatically show a welcome greeting
2. **Read the greeting** - It explains what information you need to provide
3. **See the interactive form** - Step 1 (Environment Configuration) is displayed below

### Step 1: Environment Configuration

You have two options:

#### Option A: Use Interactive Dropdowns (Recommended)
1. Select **Deployer Environment** from dropdown (MGMT, DEV, TST, PRD)
2. Select **Workload Environment** from dropdown (DEV, TST, QA, PRD)
3. Select **Azure Region** from dropdown (westeurope, northeurope, etc.)
4. Click **"✅ Submit Environment"** button

#### Option B: Type Manually
1. Scroll down to "Alternative: Manual Text Input"
2. Type in the format: `MGMT, DEV, westeurope`
3. Press Enter or click send

After submission, the app automatically moves to Step 2.

---

### Step 2: SAP System Configuration

Again, you have two options:

#### Option A: Use Interactive Inputs (Recommended)
1. **Type SAP System ID (SID)** - 3 characters, e.g., "X01" (auto-uppercased)
2. **Select SAP Product** from dropdown (S4HANA2023, S4HANA2022, etc.)
3. **Select System Sizing** from dropdown (Small, Medium, Large)
4. Optionally expand **"📊 View Sizing Details"** to see VM specifications
5. Click **"✅ Submit SAP System"** button

#### Option B: Type Manually
1. Scroll down to "Alternative: Manual Text Input"
2. Type in the format: `X01, S4HANA2023, small`
3. Press Enter or click send

After submission, your TFVARS file is generated automatically!

---

### Downloading Your Configuration

Once both steps are complete:

1. **Download button appears** at the bottom
2. Click **"📥 Download TFVARS File"** to get your `{SID}.tfvars` file
3. Optionally **expand "Preview"** to see the content before downloading
4. Optionally **expand "Configuration Summary"** to see all your inputs

---

## Chat History Management

### Viewing Previous Chats

**Left Sidebar** shows all your saved chats:
- Chats are **sorted by most recent activity**
- Each chat shows its **auto-generated title** (e.g., "S4HANA2023 X01 - westeurope")
- Timestamp shows when last updated
- **📂 icon** indicates currently active chat
- **📄 icon** indicates other saved chats

### Loading a Previous Chat

1. Find the chat in the sidebar
2. Click the chat button
3. The entire conversation and state is restored
4. You can continue where you left off or download the TFVARS again

### Deleting a Chat

1. Find the chat in the sidebar
2. Click the **🗑️ (trash)** icon next to it
3. The chat is permanently deleted
4. If you delete the currently active chat, a new chat is automatically created

### Starting a New Chat

1. Click **"➕ New Chat"** at the top of the sidebar
2. All state is reset
3. You see the welcome greeting again
4. Your previous chat is automatically saved

---

## Auto-Save Feature

The application **automatically saves** your progress:
- ✅ After completing Step 1 (Environment)
- ✅ After completing Step 2 (SAP System)
- ✅ When you click "💾 Save Current Chat" button

**You can see when it was last saved** in the sidebar under "Current Session".

**Auto-generated titles** make it easy to identify saved chats:
- Complete configs: "S4HANA2023 X01 - westeurope"
- Partial configs: "SAP Config - westeurope"
- Early stage: "Chat - 14:32"

---

## Asking Questions

You can ask questions at any time using the manual text input:

**Examples:**
- "What is a SAP SID?"
- "Which regions are available?"
- "What VM sizes are included in medium sizing?"
- "Help"
- "What can you do?"

The AI assistant will answer your question while maintaining your configuration progress.

---

## Features Overview

### 🎯 Step Indicator
Shows your progress: "Step 1/2", "Step 2/2", or "Complete"

### 🔌 Backend Status
Green = Connected | Red = Offline (with retry button)

### 💾 Manual Save
Click anytime to save your current chat

### 📋 Configuration Summary
Shows all your answers in JSON format

### 📄 TFVARS Preview
View the generated Terraform file before downloading

### 🗂️ Session ID
Every chat has a unique 8-character ID

---

## Tips and Best practices

### 1. **Use Interactive Inputs for Speed**
The dropdowns and text boxes are faster and prevent typos.

### 2. **Save Important Configurations**
Click "💾 Save Current Chat" after creating production configurations.

### 3. **Use Descriptive Information**
The auto-generated titles use your inputs, so:
- Use clear SIDs (P01 for production, D01 for dev)
- This makes finding configurations easier later

### 4. **Ask Questions**
If you're unsure about anything, just ask! The AI assistant can explain:
- SAP terminology
- VM sizing options
- Azure regions
- Best practices

### 5. **Review Before Downloading**
Always expand the "Preview TFVARS Content" to verify before downloading.

### 6. **Start New Chat for Different Configs**
Don't try to create multiple configurations in one chat. Click "New Chat" for each system.

---

## Troubleshooting

### Backend Not Connected
**Issue:** Red "Backend Offline" in sidebar

**Solutions:**
1. Wait 10-30 seconds (backend may still be starting)
2. Click "🔄 Retry Connection"
3. Check if Docker containers are running: `docker ps`
4. Restart containers: `docker compose restart`

---

### Chat Not Saving
**Issue:** Last saved timestamp doesn't update

**Solutions:**
1. Click "💾 Save Current Chat" manually
2. Complete at least one step (Environment or SAP System)
3. Check backend connection status
4. Check browser console for errors (F12)

---

### Delete Button Not Working
**Issue:** Chat still appears after clicking delete

**Solutions:**
1. Refresh the page (F5)
2. Check if you have permission to delete
3. Verify backend is connected

---

### TFVARS Not Generating
**Issue:** Download button doesn't appear after Step 2

**Solutions:**
1. Ensure you submitted **both** Step 1 and Step 2
2. Check for error messages in the chat
3. Verify SID is exactly 3 characters
4. Look for validation errors

---

## Keyboard Tips

While full keyboard shortcuts aren't implemented yet, you can use:
- **Tab**: Navigate between form fields
- **Enter**: Submit in text input field
- **Escape**: Close expandable sections
- **Space**: Toggle checkboxes/buttons when focused

---

## Data Privacy

- All data is stored in **local SQLite database** (`/data/chat_history.db`)
- No data is sent to external services (except to the local Ollama LLM)
- Sessions persist until manually deleted
- No automatic data expiration

---

## Getting Help

1. **In-Chat Help**: Type "help" or "what can you do?"
2. **Documentation**: Read IMPROVEMENTS.md for technical details
3. **Suggestions**: See SUGGESTIONS.md for feature requests
4. **Issues**: Check backend logs: `docker logs sap-agent-backend-1`

---

## Example Workflow

**Creating a Production SAP System:**

1. Click "➕ New Chat"
2. Read greeting message
3. **Step 1**: Select MGMT, PRD, westeurope → Submit
4. **Step 2**: Type "P01", select S4HANA2023, select Large → Submit
5. Review preview
6. Download "P01.tfvars"
7. Chat auto-saves with title "S4HANA2023 P01 - westeurope"

**Total time: ~30 seconds**

---

## Version Information

- **Current Version**: 2.0 (Redesigned UI)
- **Backend**: FastAPI with SQLite
- **Frontend**: Streamlit
- **LLM**: Llama 3.1 8B (via Ollama)
- **Database**: SQLite 3

---

## Next Steps

After downloading your TFVARS file:

1. Review the file contents
2. Place it in your SDAF repository
3. Run Terraform: `terraform plan -var-file={SID}.tfvars`
4. Deploy: `terraform apply -var-file={SID}.tfvars`

For more details on SDAF deployment, see the official SAP Deployment Automation Framework documentation.
