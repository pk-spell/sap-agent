# Migration Guide: Chat Agent v1 → v2

## Overview

This guide explains the key differences between the old backend (`chat_agent_simple.py`) and the new v2 backend (`chat_agent_v2.py`), and how to migrate.

---

## Key Architectural Changes

### 1. **Session-Based vs Global State**

**OLD (v1):**
```python
# Global state shared across all users
state = AgentState()

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    global state
    state.messages.append(("user", req.message))
    # ... process with global state
```

**NEW (v2):**
```python
# Each session has its own isolated state
class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.user_data: Dict = {}
        # ...

@app.post("/sessions/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    session = load_session_from_db(session_id)
    # ... process with session-specific state
```

**Why:** The old global state meant all users shared the same conversation. The new session-based approach properly isolates each user's conversation.

---

### 2. **Database Schema**

**OLD (v1):**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    title TEXT,
    messages TEXT,  -- JSON blob
    user_answers TEXT,
    tfvars_content TEXT,
    current_block TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**NEW (v2):**
```sql
-- Sessions metadata
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    title TEXT,
    current_prompt INTEGER,  -- Which of 6 prompts (0-5)
    user_data TEXT,  -- JSON of collected parameters
    tfvars_content TEXT,
    tfvars_ready BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Separate messages table with foreign key
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
)
```

**Why:** Normalized schema improves query performance and enables proper cascade deletion.

---

### 3. **Conversational Flow**

**OLD (v1):**
- Form-like: "Enter 3 comma-separated values"
- Rigid parsing: `parts = req.message.split(",")`
- Fast-path keyword matching for common questions
- 2 blocks: environment, sap_system

**NEW (v2):**
- Natural language: "Tell me about your environment in any format"
- LLM-based parsing: `await parse_environment_input(user_message)`
- 6 structured prompts matching SDAF research:
  1. Environment Identity
  2. SAP System Identity
  3. System Sizing
  4. Architecture Pattern
  5. Network Configuration
  6. Operating System Selection

**Example Old:**
```
User: "MGMT, DEV, westeurope"
Bot: "✅ Environment validated!"
```

**Example New:**
```
User: "This is a dev environment in west europe, network name SAP01"
Bot: (LLM parses) "Great! So we're setting up a DEV environment in westeurope..."
```

---

### 4. **API Endpoints**

**OLD (v1):**
```
POST /chat              # Single global chat endpoint
POST /reset             # Reset global state
POST /save-chat         # Save to database
POST /load-chat         # Load from database
GET  /list-sessions     # List all sessions
DELETE /delete-session/{id}
GET  /health
```

**NEW (v2):**
```
POST   /sessions/new               # Create new session + welcome message
GET    /sessions                   # List all sessions
GET    /sessions/{session_id}      # Get full session state
DELETE /sessions/{session_id}      # Delete session
POST   /sessions/{session_id}/chat # Send message to specific session
GET    /health                     # Health check
```

**Why:** RESTful design makes it clear which session you're interacting with.

---

### 5. **LLM Integration**

**OLD (v1):**
```python
# Only used for smalltalk/questions
if is_smalltalk(req.message):
    reply = await llm.ainvoke(prompt)
```

**NEW (v2):**
```python
# Used for ALL parsing of user input
async def parse_environment_input(user_message: str) -> Dict[str, Any]:
    prompt = f"""Extract SAP deployment parameters from:
    "{user_message}"

    Expected: environment, location, network_logical_name
    Return JSON: {{"environment": "DEV", "location": "westeurope", ...}}
    """
    response = await llm.ainvoke(prompt)
    return json.loads(response)
```

**Why:** Enables true natural language understanding instead of rigid string parsing.

---

### 6. **TFVARS Generation**

**OLD (v1):**
```python
def generate_tfvars_content(answers: Dict[str, Any]) -> str:
    # Minimal defaults from easy_defaults.yaml
    # Simple VM sizing map
    # Basic template rendering
```

**NEW (v2):**
```python
def generate_tfvars(user_data: Dict[str, Any]) -> str:
    # Load 180+ defaults from easy_defaults.yaml
    # Apply SDAF sizing dictionary (46 HANA options)
    # Set HA cluster configurations
    # Configure VM images for all tiers
    # Apply network greenfield/brownfield settings
    # Comprehensive template rendering
```

**Why:** v2 generates production-ready SDAF configurations with all required parameters.

---

## Migration Steps

### Step 1: Understand the New Flow

The new backend implements the **6-prompt conversational flow** from the SDAF research report:

1. **Prompt 0**: Environment (environment, location, network_logical_name)
2. **Prompt 1**: SAP System (sid, database_sid, database_platform)
3. **Prompt 2**: Sizing (database_size, app_tier_sizing)
4. **Prompt 3**: Architecture (standalone/distributed, HA, app server count)
5. **Prompt 4**: Network (greenfield/brownfield, subnet CIDRs)
6. **Prompt 5**: OS (SLES/RHEL version)

After Prompt 5, tfvars are automatically generated.

### Step 2: Update Frontend Calls

**OLD Frontend Code:**
```javascript
// Create session (no API call, just start chatting)
fetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ message: userInput })
})
```

**NEW Frontend Code:**
```javascript
// 1. Create new session first
const sessionResponse = await fetch('/sessions/new', { method: 'POST' });
const { session_id, message } = await sessionResponse.json();

// Display welcome message
displayMessage('assistant', message);

// 2. Send messages to specific session
fetch(`/sessions/${session_id}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message: userInput })
})
```

### Step 3: Database Migration (if needed)

If you have existing v1 sessions you want to migrate:

```python
# migration_script.py
import sqlite3
import json

old_db = sqlite3.connect("/app/data/chat_history.db")
new_db = sqlite3.connect("/app/data/chat_sessions_v2.db")

# Migrate sessions
for row in old_db.execute("SELECT * FROM sessions"):
    session_id, title, messages_json, user_answers, tfvars, block, created, updated = row

    # Parse old messages format
    messages = json.loads(messages_json)

    # Insert into new schema
    new_db.execute("""
        INSERT INTO chat_sessions (session_id, title, current_prompt, user_data, tfvars_content, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, title, 0, user_answers, tfvars, created, updated))

    # Insert messages
    for role, content in messages:
        new_db.execute("""
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (?, ?, ?)
        """, (session_id, role, content))

new_db.commit()
```

### Step 4: Docker Configuration

**Update docker-compose.yml:**

```yaml
services:
  backend:
    # ... existing config
    command: python main_v2.py  # Changed from main.py
    volumes:
      - ./backend:/app
      - ./templates:/app/templates
      - ./data:/app/data  # Persistent storage
```

### Step 5: Test the New Flow

```bash
# Start the new backend
cd /home/kuschi/sap-agent/backend
python main_v2.py

# Test with curl
curl -X POST http://localhost:8000/sessions/new

# Response:
{
  "session_id": "abc12345",
  "message": "Hi! I'll help you create an SAP deployment configuration...",
  "current_prompt": 0,
  "tfvars_ready": false
}

# Send a message
curl -X POST http://localhost:8000/sessions/abc12345/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "dev environment in westeurope, network SAP01"}'
```

---

## Feature Comparison

| Feature | v1 (Simple) | v2 (Conversational) |
|---------|-------------|---------------------|
| **Session Management** | Global state | Per-session isolation |
| **Prompts** | 2 blocks | 6 structured prompts |
| **NLP Parsing** | Keyword matching | LLM-based extraction |
| **Input Format** | Comma-separated | Natural language |
| **TFVARS Defaults** | ~20 parameters | 180+ parameters |
| **SDAF Compliance** | Basic | Production-ready |
| **Database** | Single table | Normalized schema |
| **API Design** | Stateful global | RESTful sessions |
| **HA Support** | No | Yes (cluster config) |
| **Sizing Options** | 3 profiles | 46 HANA + 3 app tier |
| **Network Modes** | Greenfield only | Greenfield + Brownfield |
| **OS Selection** | Fixed RHEL | SLES/RHEL with versions |

---

## Code Size Comparison

- **v1**: ~488 lines
- **v2**: ~950 lines

The increase is due to:
- Proper session management
- 6 LLM parsing functions
- Comprehensive TFVARS generation
- Better error handling
- Detailed prompt messages

---

## Performance Considerations

**v1 Advantages:**
- Faster (keyword matching vs LLM calls)
- Lower resource usage
- Simpler debugging

**v2 Advantages:**
- More user-friendly (natural language)
- More robust (handles varied input)
- Production-ready output
- Proper multi-user support

**Recommendation:** Use v2 for production deployments where configuration accuracy matters. Use v1 for quick demos or internal testing.

---

## Rollback Plan

If you need to rollback to v1:

```bash
# Update docker-compose.yml
command: python main.py  # Back to v1

# Or run directly
python backend/main.py
```

The old database at `/app/data/chat_history.db` remains unchanged, so v1 can resume where it left off.

---

## Common Migration Issues

### Issue 1: "Session not found"
**Cause:** Frontend trying to use old global `/chat` endpoint.
**Fix:** Update frontend to call `/sessions/new` first, then `/sessions/{id}/chat`.

### Issue 2: LLM parsing failures
**Cause:** LLM not running or unreachable.
**Fix:** Ensure Ollama is running: `curl http://localhost:11434/api/tags`

### Issue 3: Database locked
**Cause:** Both v1 and v2 trying to access same database.
**Fix:** v2 uses `chat_sessions_v2.db` to avoid conflicts.

---

## Next Steps

1. **Update Frontend:** Modify frontend to use new session-based API
2. **Test Prompts:** Walk through all 6 prompts with various inputs
3. **Validate TFVARS:** Ensure generated files work with SDAF deployer
4. **Monitor LLM:** Check LLM response times and adjust `temperature` if needed
5. **Add Validation:** Implement Azure region/SKU validation in future iteration

---

## Summary

The v2 backend represents a complete architectural redesign focused on:

✅ **Proper session isolation** (multi-user support)
✅ **Natural language understanding** (LLM-driven parsing)
✅ **SDAF compliance** (180+ defaults, production-ready)
✅ **Better UX** (conversational flow vs form-filling)
✅ **Scalability** (normalized database, RESTful API)

**Migration effort:** Medium (requires frontend updates + testing)
**Recommended for:** Production deployments, multi-user scenarios
**When to use v1:** Quick demos, single-user testing, low-resource environments

---

**Questions?** Check the inline comments in `chat_agent_v2.py` or refer to `SDAF_RESEARCH_REPORT.md` for detailed prompt design rationale.
