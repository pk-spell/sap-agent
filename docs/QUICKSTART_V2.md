# Quick Start Guide - Chat Agent v2

## Running the New Backend

### Option 1: Standalone Python

```bash
cd /home/kuschi/sap-agent/backend
python main_v2.py
```

### Option 2: Docker (Recommended)

Update your `docker-compose.yml`:

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
    command: python main_v2.py  # Changed!
    depends_on:
      - ollama
```

Then:
```bash
docker-compose up --build
```

---

## Testing the API

### 1. Create a New Session

```bash
curl -X POST http://localhost:8000/sessions/new
```

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "message": "Hi! I'll help you create an SAP deployment configuration...",
  "current_prompt": 0,
  "tfvars_ready": false
}
```

### 2. Answer Prompt 0 (Environment)

```bash
curl -X POST http://localhost:8000/sessions/a1b2c3d4/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "This is DEV in westeurope, network SAP01"}'
```

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "message": "Great! So we're setting up a DEV environment in westeurope...",
  "current_prompt": 1,
  "tfvars_ready": false,
  "user_data": {
    "environment": "DEV",
    "location": "westeurope",
    "network_logical_name": "SAP01"
  }
}
```

### 3. Answer Prompt 1 (SAP System)

```bash
curl -X POST http://localhost:8000/sessions/a1b2c3d4/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "SID X00, database HDB, using HANA"}'
```

### 4. Continue Through All 6 Prompts

- **Prompt 2**: "Development system, medium size"
- **Prompt 3**: "Standalone, no HA needed"
- **Prompt 4**: "Greenfield, defaults are fine"
- **Prompt 5**: "SUSE latest"

After Prompt 5, you'll get:

```json
{
  "session_id": "a1b2c3d4",
  "message": "Perfect! I have everything I need...",
  "current_prompt": 6,
  "tfvars_ready": true,
  "tfvars_content": "# SDAF Terraform Variables File\n..."
}
```

---

## Complete Example Session

```bash
#!/bin/bash

# 1. Create session
SESSION=$(curl -s -X POST http://localhost:8000/sessions/new | jq -r '.session_id')
echo "Created session: $SESSION"

# 2. Prompt 0: Environment
curl -s -X POST http://localhost:8000/sessions/$SESSION/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "DEV in westeurope, network SAP01"}' | jq '.message'

# 3. Prompt 1: SAP System
curl -s -X POST http://localhost:8000/sessions/$SESSION/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "X00, HDB, HANA"}' | jq '.message'

# 4. Prompt 2: Sizing
curl -s -X POST http://localhost:8000/sessions/$SESSION/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "development, medium size"}' | jq '.message'

# 5. Prompt 3: Architecture
curl -s -X POST http://localhost:8000/sessions/$SESSION/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "standalone, no HA"}' | jq '.message'

# 6. Prompt 4: Network
curl -s -X POST http://localhost:8000/sessions/$SESSION/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "greenfield, defaults"}' | jq '.message'

# 7. Prompt 5: OS
curl -s -X POST http://localhost:8000/sessions/$SESSION/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "SUSE latest"}' | jq '.message'

# 8. Get final tfvars
curl -s http://localhost:8000/sessions/$SESSION | jq -r '.tfvars_content' > sap-config.tfvars

echo "✅ TFVARS saved to sap-config.tfvars"
```

---

## Session Management

### List All Sessions

```bash
curl http://localhost:8000/sessions
```

### Get Specific Session

```bash
curl http://localhost:8000/sessions/a1b2c3d4
```

### Delete Session

```bash
curl -X DELETE http://localhost:8000/sessions/a1b2c3d4
```

---

## Natural Language Examples

The v2 backend understands various input formats:

**Prompt 0 (Environment):**
- ✅ "DEV in westeurope, network SAP01"
- ✅ "production, east us, network SAP02"
- ✅ "This is a QA environment in northeurope called SAP03"
- ✅ "dev / west europe / sap01"

**Prompt 1 (SAP System):**
- ✅ "SID X00, database HDB, HANA"
- ✅ "app sid: P01, db sid: ORA, oracle"
- ✅ "System ID is S15, database S15DB, using SQL Server"

**Prompt 2 (Sizing):**
- ✅ "development, medium size"
- ✅ "production, need large, about 1TB"
- ✅ "demo environment, keep it small"
- ✅ "This is for QA, medium should work"

**Prompt 3 (Architecture):**
- ✅ "standalone, no HA"
- ✅ "distributed with 2 app servers, yes HA"
- ✅ "distributed, 3 application servers, no high availability"

**Prompt 4 (Network):**
- ✅ "greenfield, defaults"
- ✅ "greenfield but use 10.10.x.x range"
- ✅ "brownfield"

**Prompt 5 (OS):**
- ✅ "SUSE latest"
- ✅ "Red Hat 8"
- ✅ "SLES 15 SP5"
- ✅ "RHEL 9"

---

## Troubleshooting

### LLM Not Responding

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
docker-compose up ollama
```

### Database Errors

```bash
# Check database file exists
ls -la /home/kuschi/sap-agent/backend/data/chat_sessions_v2.db

# If missing, restart backend (auto-initializes)
python main_v2.py
```

### Parse Errors

If the LLM fails to parse input, it will ask for clarification:

```
I couldn't extract all three required values. Please provide:
1. Environment (DEV/PROD/QA)
2. Azure region (westeurope, eastus, etc)
3. Network name (max 7 chars)
```

---

## Performance Tips

1. **LLM Temperature**: Lower = more consistent (default: 0.3)
2. **Cache**: LangChain caching reduces duplicate LLM calls
3. **Database**: SQLite auto-vacuums, no maintenance needed
4. **Sessions**: Delete old sessions to keep database small

---

## What's Next?

1. **Frontend Integration**: Update React/Vue frontend to use session-based API
2. **Advanced Features**:
   - Custom CIDR ranges
   - Brownfield subnet ARM IDs
   - VM SKU validation
   - Azure quota checks
3. **Export Options**: Add YAML/JSON export formats
4. **Presets**: "Dev Starter", "Prod Standard", "Enterprise HA"

---

**Ready to deploy?** See `MIGRATION_GUIDE_V2.md` for full migration instructions.
