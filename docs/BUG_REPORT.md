# Bug Report - SAP Deployment Assistant

**Test Date:** 2025-11-27 (Updated)
**Tested Version:** V3 - Lokal mit Ollama
**URLs:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

## Bug Status Summary

| Bug # | Description | Status | Verified |
|-------|-------------|--------|----------|
| 1 | Language Inconsistency (German/English) | **FIXED** | 2025-11-27 |
| 2 | OS Selection Not Applied to TFVARS | **FIXED** | 2025-11-27 |
| 3 | Duplicate Entries in TFVARS | **FIXED** | 2025-11-27 |
| 4 | Config Dashboard Missing Data | **FIXED** | 2025-11-27 |
| 5 | SID Parsing Issue | **FIXED** | 2025-11-27 |
| 6 | Console Warning on Preview | Minor - Not fixed | - |
| 7 | Database Platform Typo Not Normalized | **NEW - Open** | 2025-11-27 |

---

## Fixed Bugs

### 1. Language Inconsistency (Mixed German/English) - FIXED

**Severity:** High
**Status:** **FIXED**
**Files Modified:**
- `backend/prompts/messages.py` - Changed `get_greeting_response()` to English
- `backend/prompts/messages.py` - Changed `generate_confirmation_summary()` to English
- `backend/agent_v3_hybrid.py` - Changed line 172 ("Netzwerkname" → "Network Name")
- `backend/agent_v3_hybrid.py` - Changed lines 291-298 (architecture auto-config message to English)

**Verification:** Tested full conversation flow - all responses now in English.

---

### 2. OS Selection Not Applied to TFVARS - FIXED

**Severity:** Critical
**Status:** **FIXED**
**Files Modified:**
- `backend/tfvars/generator.py` - Added proper mapping of `os_publisher`/`os_offer` to `os_type`, `os_major_version`, `os_minor_version`

**Before:**
```
os_major_version = "RHEL"
os_minor_version = "84"
```

**After (with SUSE latest selected):**
```
os_type = "LINUX"
os_major_version = "SLES"
os_minor_version = "15-SP5"
```

**Verification:** TFVARS preview now correctly shows SLES 15-SP5 when user selects "SUSE latest".

---

### 3. Duplicate Entries in TFVARS - FIXED

**Severity:** Medium
**Status:** **FIXED**
**Files Modified:**
- `templates/sap.tfvars.j2` - Completely rewritten to remove all duplicate entries

**Original Issues:**
- `scs_high_availability` appeared twice
- `database_high_availability` appeared twice
- `enable_accelerated_networking` appeared twice
- Tags section appeared twice

**Verification:** TFVARS preview now shows clean output with no duplicates.

---

### 4. Config Dashboard Shows Missing Data - FIXED

**Severity:** High
**Status:** **FIXED**
**Files Modified:**
- `frontend-react/src/components/ConfigDashboard.tsx` - Fixed key mappings:
  - `db_sid` → `database_sid`
  - `db_platform` → `database_platform`

**Before:**
| Field | Displayed Value |
|-------|-----------------|
| SAP SID | (not set) |
| Database SID | (not set) |
| Database Platform | (not set) |

**After:**
| Field | Displayed Value |
|-------|-----------------|
| SAP SID | X00 |
| Database SID | HDB |
| Database Platform | HANA |

**Verification:** Config Dashboard now shows 95% completion with all main SAP parameters correctly displayed.

---

### 5. SAP SID Parsing Issue - FIXED

**Severity:** Medium
**Status:** **FIXED**
**Files Modified:**
- `backend/parsers/sap_system.py` - Added new regex patterns:
  - Pattern 3a: Handles "SID is X00, database HDB, using HANA" format
  - Pattern 3b: Handles "SID: X00, DB: HDB, platform: HANA" format
  - Pattern 3c: Generic labeled format fallback

**Before:**
- Input: "SID is X00, database HDB, using HANA"
- Extracted SID: `SID` (wrong - extracted the word instead of value)

**After:**
- Input: "SID is X00, database HDB, using HANA"
- Extracted SID: `X00` (correct)

**Verification:** Bot correctly confirms "We're deploying SAP **X00** with **HANA** database (**HDB**)"

---

## Minor Bugs / UI Issues (Not Fixed)

### 6. Console Warning on Preview

**Severity:** Low
**Status:** Not fixed (minor)
**Location:** Browser console

**Description:**
Warning appears when clicking Preview button:
```
No Content-Disposition header found, using fallback filename
```

This is a non-critical warning and doesn't affect functionality.

---

## New Bugs (Open)

### 7. Database Platform Typo Not Normalized

**Severity:** Low
**Status:** **NEW - Open**
**Discovered:** 2025-11-27 (Playwright Testing)
**Location:** `backend/parsers/sap_system.py`

**Description:**
When entering SAP System information, common typos for database platform are NOT normalized.

**Steps to Reproduce:**
1. Start new session
2. Enter: "LAB, northeurope, NET01" (environment step)
3. Enter: "X01, HDB, hanna" (SAP system step - note "hanna" typo)

**Expected Behavior:**
- "hanna" should be normalized to "HANA" (like other typos are handled)
- Configuration should proceed to next step

**Actual Behavior:**
- Error message: "I couldn't understand the input. Please provide valid SAP System information."
- User must re-enter with correct spelling

**Workaround:**
Use correct spelling: "HANA" instead of "hanna"

**Comparison - Working Typo Corrections:**
| Input | Normalized To | Works? |
|-------|---------------|--------|
| westeuropa | westeurope | Yes |
| developmennt | development | Yes |
| greenfild | greenfield | Yes |
| suze | SUSE | Yes |
| hanna | HANA | **No** |

**Suggested Fix:**
Add typo variants to `backend/utils/normalizer.py` `normalize_platform()` function:
```python
"hanna": "HANA",
"hana": "HANA",
"hanna database": "HANA",
```

---

## Working Features (Verified)

### Core Features
- Landing page loads correctly
- Navigation to chat works
- Full conversation flow works end-to-end
- All text is consistently in English

### Quick Templates (NEW)
- Template 1: S/4HANA Development - Works
- Template 2: S/4HANA QA/Test - Works
- Template 3: S/4HANA Production - Works
- Template 4: Demo/Sandbox - Works
- Keyword matching (e.g., "production" → Template 3) - Works

### Manual Configuration Flow
- Environment step (DEV, QA, PROD, LAB, etc.) - Works
- SAP System step (SID, DB SID, Platform) - Works
- Sizing step (purpose + DB size) - Works
- Architecture step (standalone/distributed) - Works
- Network step (greenfield/brownfield) - Works
- OS Selection step (SUSE/RHEL) - Works
- Confirmation step - Works
- TFVARS generation - Works

### Typo Normalization (NEW)
- Region: "westeuropa" → "westeurope" - Works
- Purpose: "developmennt" → "development" - Works
- Network: "greenfild" → "greenfield" - Works
- OS: "suze" → "SUSE" - Works

### Session Management
- Session creation works
- Session switching works (chat history preserved)
- Session deletion with confirmation dialog works
- Session search/filter works (shows result count)
- Clear search button works

### UI Controls
- Dark mode toggle works
- Font size button present
- High contrast button present
- Progress bar updates correctly during conversation
- Step indicators (checkmarks) work

### TFVARS Features
- Preview TFVARS dialog opens and displays correct content
- View Config dashboard opens and displays collected values
- Export JSON button present
- Download button works
- Share session button present

---

## Test Environment

- **Platform:** Linux (WSL2)
- **Browser:** Chromium (Playwright)
- **Docker:** Running via docker compose
- **LLM:** Ollama (llama3.1:8b) on localhost:11434
- **Testing Tool:** Playwright MCP

---

## Conclusion

All 5 critical/high-severity bugs from previous testing have been fixed and verified.

**New features verified working:**
- Quick-select templates (1-4)
- Input normalization with typo correction
- Manual 6-step configuration flow
- Session management (create, switch, search, delete)

**One new low-severity bug found:**
- Bug #7: Database platform typo "hanna" not normalized to "HANA"

The application is stable and ready for use. The remaining bugs (#6, #7) are low severity and do not affect core functionality.
