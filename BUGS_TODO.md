# BUGS & TODO - Stand 2025-11-24

## 🐛 Kritische Bugs (für morgen)

### 1. State wird nicht neu geladen bei Session-Wechsel
**Problem:** Wenn man auf eine alte Session klickt oder neue Session erstellt, wird der Chat-State nicht zurückgesetzt
- Progress Bar bleibt bei 100%
- TFVARS Ready Status bleibt aktiv
- Chat zeigt alte Messages

**Wo:** `frontend-react/src/App.tsx` - handleSelectSession() funktioniert nicht richtig
**Fix:** ChatWindow muss bei sessionId-Änderung komplett neu mounten

---

### 2. Download Dateiname ist falsch
**Problem:** Download-Datei heißt `sap-deployment-12466...` statt korrektem SDAF-Namen
- Backend gibt korrekten Filename im Content-Disposition Header zurück
- Frontend parst Header nicht richtig oder verwendet Fallback

**Wo:**
- `frontend-react/src/api/client.ts:125-133` - Content-Disposition Parsing
- Backend `main_v3.py:329` - FileResponse mit filename parameter

**Erwarteter Name:** `DEV-WEEU-SAP01-X00.tfvars`
**Aktueller Name:** `sap-deployment-12466.tfvars`

**Fix:** Content-Disposition Header Parsing überprüfen oder direkt filename vom Backend API holen

---

### 3. Network Name kann übersprungen werden
**Problem:** User konnte zum zweiten Schritt (SAP System) ohne `network_logical_name` einzugeben
- Parser erkennt fehlende Pflichtfelder nicht richtig
- Progressive Questioning erlaubt Weitergehen trotz fehlender Werte

**Wo:** `backend/agent_v3_hybrid.py` - Prompt 0 (Environment) Validation
**Fix:** Strikte Validierung: `has_env AND has_location AND has_network` bevor Prompt 1

---

## ✅ Was heute funktioniert

- Sessions werden gespeichert und angezeigt
- Delete Button erscheint on hover
- Download Button im Chat vorhanden
- Backend gibt korrekte SDAF-Filenames zurück
- Grouped Questioning funktioniert größtenteils
- SQLite Persistence läuft

---

## 🔮 Features für später (Nice-to-Have)

### Preview Button für TFVARS
- Button neben Download im Chat
- Zeigt TFVARS Content in Modal/Popup
- Read-only Code-Ansicht

### Besseres Delete-Confirmation Design
- Aktuell: Standard browser confirm()
- Ziel: Fluent UI Dialog mit Bestätigung

### Button oben rechts entfernen?
- Wenn Chat-Download gut funktioniert
- Nur noch im Chat, nicht Header
- User-Feedback abwarten

---

## 📝 Notizen

**Aktueller Stand:**
- V3 Backend mit Hybrid Agent (V2 Logic + V3 LLM-Factory)
- React Frontend mit Fluent UI
- SQLite Session Persistence
- SDAF-compliant Filenames (Backend)
- Gruppierte Fragen (2-3 Werte pro Prompt)

**Letzte Commits:**
- a14ca89 - Session list display fix
- 0b0a0fb - Delete button hover fix
- ad18d58 - Session refresh + TFVARS filename + Chat download

**Nächste Session:**
1. Session State Refresh debuggen
2. Download Filename Parsing fixen
3. Network Name Validation verschärfen
4. Testen mit vollständigem Flow
