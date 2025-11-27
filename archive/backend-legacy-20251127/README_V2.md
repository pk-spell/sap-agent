# SDAF Chat Agent v2 - Backend Documentation

## Overview

The v2 backend implements a **session-based, LLM-driven conversational agent** for generating SDAF-compliant Terraform variable files. It follows the 6-prompt flow defined in the SDAF research report.

---

## Architecture

### Core Components

```
chat_agent_v2.py
├── Session Management
│   └── ChatSession class (isolated state per user)
├── Database Layer
│   ├── chat_sessions (metadata)
│   └── chat_messages (conversation history)
├── LLM Parsing Functions
│   ├── parse_environment_input()
│   ├── parse_sap_system_input()
│   ├── parse_sizing_input()
│   ├── parse_architecture_input()
│   ├── parse_network_input()
│   └── parse_os_input()
├── Prompt Definitions
│   └── get_prompt_message(0-5)
├── TFVARS Generation
│   ├── load_defaults()
│   └── generate_tfvars()
└── FastAPI Endpoints
    ├── POST /sessions/new
    ├── GET  /sessions
    ├── GET  /sessions/{id}
    ├── POST /sessions/{id}/chat
    └── DELETE /sessions/{id}
```

### Data Flow

```
User Input
    ↓
FastAPI Endpoint (/sessions/{id}/chat)
    ↓
Load Session from SQLite
    ↓
Add User Message to Session
    ↓
LLM Parsing (ainvoke)
    ↓
Extract Structured Parameters
    ↓
Validate & Update Session State
    ↓
Generate Next Prompt / TFVARS
    ↓
Save Session to SQLite
    ↓
Return Response to User
```

---

## Session Lifecycle

### 1. Creation

```python
POST /sessions/new
→ Generate UUID
→ Create ChatSession object
→ Add welcome message (Prompt 0)
→ Save to database
→ Return session_id + welcome
```

### 2. Conversation

```python
POST /sessions/{id}/chat
→ Load session from database
→ Add user message
→ Parse message with LLM (based on current_prompt)
→ Extract parameters → user_data
→ Advance to next prompt
→ Add assistant response
→ Save session
→ Return response
```

### 3. Completion

```python
After Prompt 5:
→ Set current_prompt = 6
→ Generate TFVARS from user_data + defaults
→ Set tfvars_ready = true
→ Return final summary + tfvars_content
```

### 4. Cleanup

```python
DELETE /sessions/{id}
→ Delete from chat_sessions
→ Cascade delete from chat_messages
→ Return success
```

---

## Database Schema

### chat_sessions

| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT PRIMARY KEY | Unique session identifier |
| title | TEXT | Auto-generated title (e.g., "SAP X00 - DEV - westeurope") |
| current_prompt | INTEGER | Current prompt index (0-6) |
| user_data | TEXT | JSON of collected parameters |
| tfvars_content | TEXT | Generated tfvars file |
| tfvars_ready | BOOLEAN | Whether generation is complete |
| created_at | TIMESTAMP | Session creation time |
| updated_at | TIMESTAMP | Last activity time |

### chat_messages

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment message ID |
| session_id | TEXT | Foreign key to chat_sessions |
| role | TEXT | "user" or "assistant" |
| content | TEXT | Message text |
| timestamp | TIMESTAMP | Message time |

---

## Prompt Flow

### Prompt 0: Environment Identity

**Collects:**
- `environment` (DEV/PROD/QA/etc)
- `location` (westeurope/eastus/etc)
- `network_logical_name` (SAP01/SAP02/etc)

**Parsing:**
```python
await parse_environment_input(user_message)
→ LLM extracts JSON: {"environment": "DEV", "location": "westeurope", ...}
```

**Validation:**
- Environment: max 5 chars, uppercase
- Location: valid Azure region
- Network name: max 7 chars

---

### Prompt 1: SAP System Identity

**Collects:**
- `sid` (3-char SAP SID)
- `database_sid` (database SID)
- `database_platform` (HANA/ORACLE/SQLSERVER/etc)

**Parsing:**
```python
await parse_sap_system_input(user_message)
→ {"sid": "X00", "database_sid": "HDB", "database_platform": "HANA"}
```

---

### Prompt 2: System Sizing

**Collects:**
- `database_size` (Demo/E32ds_v4/M64s/etc)
- `app_tier_sizing_dictionary_key` (Optimized/Production)
- `purpose` (development/production/etc)

**Parsing:**
```python
await parse_sizing_input(user_message)
→ Maps user intent to SDAF sizing keys
→ "development, medium" → {"database_size": "E32ds_v4", "app_tier_sizing": "Optimized"}
```

**Sizing Map:**
| User Intent | Database Size | App Tier |
|-------------|---------------|----------|
| Demo/Testing | Demo / S4Demo | Default |
| Development | E20ds_v4 / E32ds_v4 | Optimized |
| QA/Staging | E48ds_v4 / E64ds_v4 | Optimized |
| Production | M64s / M64ls | Production |
| High-Load Prod | M128s+ | Production |

---

### Prompt 3: Architecture Pattern

**Collects:**
- `deployment_type` (standalone/distributed)
- `ha_required` (true/false)
- `application_server_count` (0 for standalone, 1-N for distributed)
- `scs_server_count` (1 or 2 if HA)
- `database_server_count` (1 or 2 if HA)
- `database_high_availability` (true/false)
- `scs_high_availability` (true/false)

**Logic:**

**Standalone:**
```python
enable_app_tier_deployment = False
application_server_count = 0
scs_server_count = 1
database_server_count = 1
*_high_availability = False
```

**Distributed (no HA):**
```python
enable_app_tier_deployment = True
application_server_count = user input (1-N)
scs_server_count = 1
database_server_count = 1
*_high_availability = False
```

**Distributed (with HA):**
```python
enable_app_tier_deployment = True
application_server_count = user input
scs_server_count = 2
database_server_count = 2
database_high_availability = True
scs_high_availability = True
```

---

### Prompt 4: Network Configuration

**Collects:**
- `network_type` (greenfield/brownfield)
- Subnet CIDRs (if greenfield + custom)

**Default Greenfield Subnets:**
```
admin_subnet_address_prefix = "10.1.0.0/24"
db_subnet_address_prefix    = "10.1.1.0/24"
app_subnet_address_prefix   = "10.1.2.0/24"
web_subnet_address_prefix   = "10.1.3.0/24"
```

**Brownfield:** (Future enhancement - collect ARM IDs)

---

### Prompt 5: Operating System

**Collects:**
- `os_publisher` (SUSE/RedHat)
- `os_offer` (sles-sap-15-sp5/RHEL-SAP-HA)
- `os_sku` (gen2/8.6/9_0/etc)

**VM Image Configuration:**
```python
{
  "os_type": "LINUX",
  "publisher": "SUSE",
  "offer": "sles-sap-15-sp5",
  "sku": "gen2",
  "version": "latest",
  "type": "marketplace"
}
```

This is applied to:
- `database_vm_image`
- `scs_server_image`
- `application_server_image`
- `webdispatcher_server_image`

---

## TFVARS Generation

### Defaults Loading

```python
config = load_defaults()  # From easy_defaults.yaml
```

Provides 180+ default values:
- HA cluster settings (AFA, Premium_ZRS)
- VM placement (PPG, zones)
- Network (DHCP, dual NICs)
- Storage (AFS, volume sizes)
- Security (SSH key auth)
- Monitoring (disabled by default)
- Tags (DeployedBy: "SDAF-ChatAgent")

### User Data Application

```python
# Override defaults with collected parameters
config["environment"] = user_data["environment"]
config["location"] = user_data["location"]
config["sid"] = user_data["sid"]
config["database_size"] = user_data["database_size"]
# ... etc for all collected values
```

### Template Rendering

```python
template = jinja_env.get_template("sap.tfvars.j2")
tfvars = template.render(config=config)
```

---

## LLM Integration

### Configuration

```python
llm = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434",
    temperature=0.3  # Lower = more deterministic
)
```

### Parsing Pattern

```python
async def parse_environment_input(user_message: str) -> Dict[str, Any]:
    prompt = f"""Extract SAP deployment parameters from:
    "{user_message}"

    Expected: environment, location, network_logical_name
    Return ONLY valid JSON: {{"environment": "DEV", ...}}
    """

    response = await llm.ainvoke(prompt)

    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())

    return {}  # Fallback
```

### Error Handling

```python
try:
    parsed = await parse_environment_input(user_message)
    if not parsed.get("environment"):
        # Ask for clarification
        return "I couldn't extract the environment. Please provide..."
except Exception as e:
    logger.error(f"Parse error: {e}")
    return "Sorry, I had trouble understanding. Please try again..."
```

---

## API Reference

### POST /sessions/new

**Create new chat session**

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "message": "Hi! I'll help you create...",
  "current_prompt": 0,
  "tfvars_ready": false
}
```

---

### GET /sessions

**List all sessions**

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "a1b2c3d4",
      "title": "SAP X00 - DEV - westeurope",
      "current_prompt": 6,
      "tfvars_ready": true,
      "created_at": "2025-01-15T10:00:00",
      "updated_at": "2025-01-15T10:05:00"
    }
  ]
}
```

---

### GET /sessions/{session_id}

**Get full session state**

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "messages": [
    {"role": "assistant", "content": "Hi! I'll help you..."},
    {"role": "user", "content": "DEV in westeurope..."},
    ...
  ],
  "current_prompt": 6,
  "user_data": {
    "environment": "DEV",
    "location": "westeurope",
    ...
  },
  "tfvars_ready": true,
  "tfvars_content": "# SDAF Terraform...",
  "title": "SAP X00 - DEV - westeurope",
  "created_at": "2025-01-15T10:00:00",
  "updated_at": "2025-01-15T10:05:00"
}
```

---

### POST /sessions/{session_id}/chat

**Send message to session**

**Request:**
```json
{
  "message": "DEV in westeurope, network SAP01"
}
```

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "message": "Great! So we're setting up...",
  "current_prompt": 1,
  "tfvars_ready": false,
  "tfvars_content": "",
  "user_data": {
    "environment": "DEV",
    "location": "westeurope",
    "network_logical_name": "SAP01"
  }
}
```

---

### DELETE /sessions/{session_id}

**Delete a session**

**Response:**
```json
{
  "status": "deleted",
  "session_id": "a1b2c3d4"
}
```

---

## Configuration

### Environment Variables

```bash
# LLM Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TEMPERATURE=0.3

# Database
DB_PATH=/app/data/chat_sessions_v2.db

# Templates
TEMPLATES_DIR=/app/templates
```

### Files Structure

```
/app/
├── chat_agent_v2.py      # Main application
├── main_v2.py            # Entry point
├── templates/
│   ├── sap.tfvars.j2     # TFVARS template
│   └── easy_defaults.yaml # Default values
└── data/
    └── chat_sessions_v2.db # SQLite database
```

---

## Testing

### Unit Tests

```python
# test_chat_agent_v2.py
import pytest
from chat_agent_v2 import ChatSession, parse_environment_input

def test_session_creation():
    session = ChatSession("test123")
    assert session.session_id == "test123"
    assert session.current_prompt == 0
    assert len(session.messages) == 0

@pytest.mark.asyncio
async def test_environment_parsing():
    result = await parse_environment_input("DEV in westeurope, network SAP01")
    assert result["environment"] == "DEV"
    assert result["location"] == "westeurope"
    assert result["network_logical_name"] == "SAP01"
```

### Integration Tests

```bash
# test_api.sh
#!/bin/bash

# 1. Health check
curl http://localhost:8000/health

# 2. Create session
SESSION=$(curl -s -X POST http://localhost:8000/sessions/new | jq -r '.session_id')

# 3. Complete flow
curl -X POST http://localhost:8000/sessions/$SESSION/chat \
  -d '{"message": "DEV in westeurope, SAP01"}'

# ... continue through all prompts

# 4. Verify tfvars
curl http://localhost:8000/sessions/$SESSION | jq '.tfvars_ready'
# Should be true
```

---

## Performance

### Benchmarks

| Operation | Avg Time | Notes |
|-----------|----------|-------|
| Create session | ~10ms | Database insert |
| LLM parsing | ~500-2000ms | Depends on Ollama load |
| TFVARS generation | ~50ms | Template rendering |
| Save session | ~20ms | SQLite write |
| Load session | ~15ms | SQLite read |

### Optimization Tips

1. **LLM Caching**: LangChain caches identical prompts
2. **Database Indexing**: Session ID is primary key (fast lookup)
3. **Async Operations**: All LLM calls use `ainvoke`
4. **Connection Pooling**: SQLite auto-manages connections

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main_v2.py"]
```

### Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./templates:/app/templates
      - ./data:/app/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

---

## Troubleshooting

### Issue: LLM not responding

**Check:** Ollama is running
```bash
curl http://localhost:11434/api/tags
```

**Fix:** Start Ollama
```bash
docker-compose up ollama
```

---

### Issue: Database locked

**Check:** No other processes using DB
```bash
lsof /app/data/chat_sessions_v2.db
```

**Fix:** Ensure single backend instance

---

### Issue: Parse failures

**Check:** LLM temperature and prompts
```python
# Lower temperature for more deterministic parsing
llm = OllamaLLM(temperature=0.1)  # Try 0.1 instead of 0.3
```

---

## Future Enhancements

1. **Brownfield Support**: Collect Azure ARM IDs for existing subnets
2. **Validation**: Azure region/SKU availability checks
3. **Export Formats**: YAML, JSON, Excel
4. **Presets**: Pre-configured templates ("Dev Starter", "Prod HA")
5. **Cost Estimation**: Show estimated Azure costs
6. **Deployment Integration**: Direct Terraform execution
7. **Multi-language**: i18n support
8. **Voice Input**: Speech-to-text integration

---

## References

- **SDAF Research Report**: `/home/kuschi/sap-agent/SDAF_RESEARCH_REPORT.md`
- **Migration Guide**: `/home/kuschi/sap-agent/MIGRATION_GUIDE_V2.md`
- **Quick Start**: `/home/kuschi/sap-agent/QUICKSTART_V2.md`
- **SDAF Official Docs**: https://learn.microsoft.com/en-us/azure/sap/automation/

---

**Version**: 2.0.0
**Last Updated**: 2025-01-15
**Maintainer**: SDAF Chat Agent Team
