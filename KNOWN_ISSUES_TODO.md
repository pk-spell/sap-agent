# Known Issues & TODO für morgen

## 🐛 Aktuelles Problem: LLM Timeout beim Parsing

### Symptom
```
User Input: "This is dev in westeurope" (nur 2 von 3 Werten)
Fehler: HTTPConnectionPool(host='backend', port=8000): Read timed out. (read timeout=30)
```

### Ursachenanalyse

**Wahrscheinlichste Ursachen:**

1. **LLM zu langsam**
   - llama3.1:8b braucht >30 Sekunden für JSON Extraktion
   - Besonders bei unvollständigen/mehrdeutigen Inputs
   - CPU-only Inferenz auf dem Host ist langsam

2. **LLM hängt bei unvollständigen Inputs**
   - Prompt erwartet 3 Werte (environment, location, network_name)
   - User gibt nur 2 ("dev in westeurope")
   - LLM "grübelt" zu lange wie es den fehlenden Wert extrahieren soll
   - JSON Parsing im Backend wartet endlos

3. **Keine Timeout Handling im LLM Call**
   - `await llm.ainvoke(prompt)` hat kein Timeout
   - Wenn LLM hängt, wartet der Request ewig
   - Frontend timeout (30s) greift zuerst

### 💡 Lösungsvorschläge für morgen

#### Option 1: Schnelleres LLM verwenden ⭐ (EMPFOHLEN)

**Problem:** llama3.1:8b ist zu langsam für Parsing
**Lösung:** Wechsel zu einem schnelleren Modell

```bash
# Kleineres, schnelleres Modell
ollama pull llama3.2:3b       # Nur 3B Parameter, viel schneller
ollama pull phi3:mini         # Microsoft's Mini-Modell, sehr schnell
ollama pull gemma2:2b         # Google's 2B Modell

# In backend/chat_agent_v2.py ändern:
llm = OllamaLLM(
    model="llama3.2:3b",  # Statt llama3.1:8b
    base_url="http://host.docker.internal:11434",
    async_mode=True
)
```

**Vorteile:**
- ✅ Viel schneller (<5 Sekunden statt >30)
- ✅ Kleinere Modelle sind oft gut genug für strukturierte Extraktion
- ✅ Keine Code-Änderungen nötig außer Modellname

**Nachteil:**
- ⚠️ Möglicherweise schlechtere Parsing-Qualität bei komplexen Inputs

---

#### Option 2: LLM Timeout hinzufügen

**Problem:** LLM Call hat kein Timeout
**Lösung:** Timeout für alle LLM Calls setzen

```python
# In backend/chat_agent_v2.py

import asyncio

async def parse_environment_input(user_message: str) -> dict:
    prompt = f"""..."""

    try:
        # Timeout nach 15 Sekunden
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=15.0
        )
        return json.loads(response)
    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout for input: {user_message}")
        # Fallback: Versuche einfaches Regex Parsing
        return fallback_regex_parse(user_message)
    except Exception as e:
        logger.error(f"LLM parsing error: {e}")
        return fallback_regex_parse(user_message)
```

**Vorteile:**
- ✅ Verhindert endloses Warten
- ✅ Fallback Mechanismus für Robustheit
- ✅ Bessere Error Messages für User

**Nachteil:**
- ⚠️ Benötigt Fallback Parsing Logik (Regex/String Split)

---

#### Option 3: Hybrid Parsing (LLM + Regex Fallback) ⭐ (BESTE LANGFRISTIGE LÖSUNG)

**Problem:** Pure LLM Parsing ist langsam und kann fehlschlagen
**Lösung:** Intelligente Kombination aus schnellem Regex und LLM

```python
async def parse_environment_input(user_message: str) -> dict:
    # STUFE 1: Schneller Regex Check für einfache Fälle
    simple_patterns = {
        # "DEV, westeurope, SAP01" Format
        r'^(\w+)\s*,\s*(\w+)\s*,\s*(\w+)$': lambda m: {
            "environment": m.group(1).upper(),
            "location": normalize_location(m.group(2)),
            "network_logical_name": m.group(3).upper()
        },
        # "dev in westeurope network SAP01" Format
        r'(\w+)\s+in\s+(\w+)\s+network\s+(\w+)': lambda m: {
            "environment": m.group(1).upper(),
            "location": normalize_location(m.group(2)),
            "network_logical_name": m.group(3).upper()
        }
    }

    for pattern, extractor in simple_patterns.items():
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            logger.info(f"✅ Fast regex parsing succeeded")
            return extractor(match)

    # STUFE 2: Komplexer Input → LLM mit Timeout
    logger.info(f"⏱️ Using LLM for complex input")
    try:
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=15.0
        )
        return json.loads(response)
    except:
        # STUFE 3: Finale Fallback - frage User nach
        return {"error": "unclear", "message": "I didn't understand that. Please provide: environment, location, network name"}
```

**Vorteile:**
- ✅ Schnell bei einfachen Inputs (99% der Fälle)
- ✅ Intelligent bei komplexen Inputs
- ✅ Robuster Fallback
- ✅ Beste User Experience

**Nachteil:**
- ⚠️ Mehr Code zu maintainen

---

#### Option 4: Frontend Timeout erhöhen

**Quick & Dirty Fix:** Erhöhe Frontend Timeout

```python
# In frontend/chat_v2.py
response = requests.post(
    f"{API_URL}/sessions/{session_id}/chat",
    json={"message": user_input},
    timeout=60  # Von 30 auf 60 Sekunden
)
```

**Vorteile:**
- ✅ Minimale Änderung
- ✅ Funktioniert wenn LLM nur etwas langsam ist

**Nachteile:**
- ❌ Löst das eigentliche Problem nicht
- ❌ User wartet noch länger
- ❌ Schlechte UX

---

#### Option 5: Verwende OpenAI API statt Ollama 💰

**Problem:** Lokale LLMs sind langsam
**Lösung:** Wechsel zu Cloud LLM

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",  # Schnell & günstig
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)
```

**Vorteile:**
- ✅ Extrem schnell (<2 Sekunden)
- ✅ Sehr gute Parsing Qualität
- ✅ Skalierbar

**Nachteile:**
- ❌ Kostet Geld (~$0.15 per 1M input tokens)
- ❌ Braucht Internet
- ❌ Datenschutz (User Inputs gehen zu OpenAI)

---

### 🎯 Empfohlener Ansatz für morgen

**Phase 1: Quick Win (10 Minuten)**
```bash
# Schnelleres Modell testen
ollama pull llama3.2:3b
# Oder
ollama pull phi3:mini

# In backend/chat_agent_v2.py Zeile 23 ändern:
model="llama3.2:3b"
```

**Phase 2: Robustheit (30 Minuten)**
- LLM Timeouts hinzufügen (15 Sekunden)
- Einfaches Regex Fallback implementieren
- Bessere Error Messages für User

**Phase 3: Production Ready (2 Stunden)**
- Hybrid Parsing (Regex + LLM)
- Umfassende Error Handling
- User Feedback bei unklar ("Did you mean...?")

---

### 📊 Performance Benchmarks (zum Testen morgen)

```bash
# Test verschiedene Modelle
# In backend/chat_agent_v2.py model= ändern und jeweils testen:

llama3.1:8b      → Erwartung: 20-40s  (AKTUELL - ZU LANGSAM)
llama3.2:3b      → Erwartung: 3-8s   (EMPFOHLEN)
phi3:mini        → Erwartung: 2-5s   (SCHNELLSTE)
gemma2:2b        → Erwartung: 2-6s   (ALTERNATIVE)
gpt-4o-mini      → Erwartung: 1-3s   (CLOUD, KOSTET GELD)
```

**Test Script:**
```bash
# Zeit messen
time curl -X POST http://localhost:8000/sessions/{id}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "dev in westeurope network SAP01"}'
```

---

### 🔍 Debugging Tipps für morgen

1. **Check Ollama Performance:**
```bash
# Wie lange braucht Ollama direkt?
time ollama run llama3.1:8b "Extract JSON: environment, location, network from 'dev in westeurope'"
```

2. **Backend Logs mit Timestamps:**
```bash
docker compose logs -f backend | ts
# Zeigt genau wo die Zeit verloren geht
```

3. **LLM Call instrumentieren:**
```python
import time

async def parse_environment_input(user_message: str) -> dict:
    start = time.time()
    logger.info(f"⏱️ Starting LLM parsing...")

    response = await llm.ainvoke(prompt)

    elapsed = time.time() - start
    logger.info(f"⏱️ LLM took {elapsed:.2f}s")

    return json.loads(response)
```

---

### 💡 Weitere Verbesserungen (Nice to Have)

1. **Streaming Response**
   - LLM streamt Antwort während es denkt
   - User sieht "Assistant is thinking..." mit Dots Animation
   - Bessere UX auch bei langsamem LLM

2. **Caching häufiger Patterns**
   - "dev in westeurope" wurde schon mal geparst → Cache Result
   - Redis oder In-Memory Cache
   - Massive Speed Improvement bei wiederkehrenden Inputs

3. **Progressive Prompting**
   - Frage fehlende Werte nach statt zu raten
   - "I got dev and westeurope. What's the network name?"
   - Besser als lange LLM "Grübel-Zeit"

---

## 📝 Zusammenfassung

**Das Problem:** llama3.1:8b ist zu langsam für Production Use (>30s)

**Beste Lösung:**
1. **Kurzfristig:** Wechsel zu llama3.2:3b oder phi3:mini (5 Minuten)
2. **Mittelfristig:** Hybrid Parsing (Regex + LLM mit Timeout)
3. **Langfristig:** Evaluate gpt-4o-mini für Demo/Production

**Action Items für morgen:**
- [ ] Teste llama3.2:3b
- [ ] Teste phi3:mini
- [ ] Benchmark beide Modelle
- [ ] Wenn schnell genug → fertig
- [ ] Wenn nicht → Implementiere Timeouts + Fallback

**Zeitaufwand:** 30-60 Minuten je nach gewähltem Ansatz
