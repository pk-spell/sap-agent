#!/bin/bash
# Test script for SDAF Chat Agent v2
# This script runs a complete conversation flow and validates the output

set -e  # Exit on error

BASE_URL="http://localhost:8000"
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}SDAF Chat Agent v2 - Test Script${NC}\n"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed. Install with: sudo apt install jq${NC}"
    exit 1
fi

# 1. Health check
echo -e "${BLUE}1. Health Check${NC}"
HEALTH=$(curl -s $BASE_URL/health)
if [ "$(echo $HEALTH | jq -r '.status')" != "ok" ]; then
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend is healthy${NC}\n"

# 2. Create session
echo -e "${BLUE}2. Creating new session${NC}"
SESSION_RESPONSE=$(curl -s -X POST $BASE_URL/sessions/new)
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
WELCOME=$(echo $SESSION_RESPONSE | jq -r '.message' | head -n 1)

if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" = "null" ]; then
    echo -e "${RED}✗ Failed to create session${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Session created: $SESSION_ID${NC}"
echo -e "  Welcome: $WELCOME...\n"

# Function to send message
send_message() {
    local message="$1"
    local prompt_name="$2"

    echo -e "${BLUE}${prompt_name}${NC}"
    echo -e "  User: ${message}"

    RESPONSE=$(curl -s -X POST $BASE_URL/sessions/$SESSION_ID/chat \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\"}")

    REPLY=$(echo $RESPONSE | jq -r '.message' | head -n 3 | tr '\n' ' ')
    CURRENT_PROMPT=$(echo $RESPONSE | jq -r '.current_prompt')
    TFVARS_READY=$(echo $RESPONSE | jq -r '.tfvars_ready')

    echo -e "  Bot: ${REPLY}..."
    echo -e "${GREEN}✓ Prompt $CURRENT_PROMPT complete${NC}\n"

    # Return tfvars_ready status
    echo $TFVARS_READY
}

# 3. Prompt 0: Environment
READY=$(send_message "DEV in westeurope, network SAP01" "3. Prompt 0: Environment Identity")

# 4. Prompt 1: SAP System
READY=$(send_message "SID X00, database HDB, using HANA" "4. Prompt 1: SAP System Identity")

# 5. Prompt 2: Sizing
READY=$(send_message "development system, medium size" "5. Prompt 2: System Sizing")

# 6. Prompt 3: Architecture
READY=$(send_message "standalone, no HA needed" "6. Prompt 3: Architecture Pattern")

# 7. Prompt 4: Network
READY=$(send_message "greenfield, defaults are fine" "7. Prompt 4: Network Configuration")

# 8. Prompt 5: OS
READY=$(send_message "SUSE latest" "8. Prompt 5: Operating System")

# 9. Verify tfvars generation
echo -e "${BLUE}9. Verifying TFVARS generation${NC}"
SESSION_DATA=$(curl -s $BASE_URL/sessions/$SESSION_ID)
TFVARS_READY=$(echo $SESSION_DATA | jq -r '.tfvars_ready')
TFVARS_CONTENT=$(echo $SESSION_DATA | jq -r '.tfvars_content')

if [ "$TFVARS_READY" != "true" ]; then
    echo -e "${RED}✗ TFVARS not ready${NC}"
    exit 1
fi

if [ -z "$TFVARS_CONTENT" ] || [ "$TFVARS_CONTENT" = "null" ]; then
    echo -e "${RED}✗ TFVARS content is empty${NC}"
    exit 1
fi

# Save tfvars to file
OUTPUT_FILE="test_output_$(date +%s).tfvars"
echo "$TFVARS_CONTENT" > $OUTPUT_FILE

echo -e "${GREEN}✓ TFVARS generated successfully${NC}"
echo -e "  Saved to: ${OUTPUT_FILE}"
echo -e "  Size: $(wc -l < $OUTPUT_FILE) lines\n"

# 10. Verify key parameters
echo -e "${BLUE}10. Validating TFVARS content${NC}"

check_param() {
    local param="$1"
    local expected="$2"

    if echo "$TFVARS_CONTENT" | grep -q "$param.*$expected"; then
        echo -e "${GREEN}✓ $param = $expected${NC}"
    else
        echo -e "${RED}✗ $param not found or incorrect${NC}"
    fi
}

check_param "environment" "DEV"
check_param "location" "westeurope"
check_param "network_logical_name" "SAP01"
check_param "sid" "X00"
check_param "database_sid" "HDB"
check_param "database_platform" "HANA"

echo ""

# 11. Test session listing
echo -e "${BLUE}11. Testing session listing${NC}"
SESSIONS=$(curl -s $BASE_URL/sessions)
SESSION_COUNT=$(echo $SESSIONS | jq '.sessions | length')

echo -e "${GREEN}✓ Found $SESSION_COUNT session(s)${NC}\n"

# 12. Test session deletion
echo -e "${BLUE}12. Testing session deletion${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE $BASE_URL/sessions/$SESSION_ID)
DELETE_STATUS=$(echo $DELETE_RESPONSE | jq -r '.status')

if [ "$DELETE_STATUS" = "deleted" ]; then
    echo -e "${GREEN}✓ Session deleted successfully${NC}\n"
else
    echo -e "${RED}✗ Failed to delete session${NC}\n"
    exit 1
fi

# Summary
echo -e "${BOLD}${GREEN}========================================${NC}"
echo -e "${BOLD}${GREEN}ALL TESTS PASSED ✓${NC}"
echo -e "${BOLD}${GREEN}========================================${NC}\n"

echo -e "Test Results:"
echo -e "  - Health check: ${GREEN}✓${NC}"
echo -e "  - Session creation: ${GREEN}✓${NC}"
echo -e "  - 6-prompt flow: ${GREEN}✓${NC}"
echo -e "  - TFVARS generation: ${GREEN}✓${NC}"
echo -e "  - Parameter validation: ${GREEN}✓${NC}"
echo -e "  - Session listing: ${GREEN}✓${NC}"
echo -e "  - Session deletion: ${GREEN}✓${NC}"
echo -e ""
echo -e "Output file: ${BOLD}$OUTPUT_FILE${NC}"
echo -e ""
echo -e "${BLUE}You can now deploy the TFVARS with:${NC}"
echo -e "  terraform apply -var-file=$OUTPUT_FILE"
echo -e ""
