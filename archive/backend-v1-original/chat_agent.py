from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Dict, Any
import operator
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging

# Setup
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="SDAF Chat Agent")
llm = OllamaLLM(model="llama3.1:8b", base_url="http://host.docker.internal:11434")
templates_dir = Path("/app/templates")
jinja_env = Environment(loader=FileSystemLoader(templates_dir))

# LangGraph State
class AgentState(TypedDict):
    messages: Annotated[List[tuple], operator.add]  # (role, content)
    current_block: str
    user_answers: Dict[str, Any]
    tfvars_ready: bool

# Nodes
def ask_environment(state: AgentState):
    q = """🌍 **Environment Block** - Gib kommagetrennt:
1. Deployer (MGMT/DEV/TST/PRD)
2. Workload (DEV/TST/PRD)  
3. Region (westeurope/northeurope/germanywestcentral)
**Beispiel**: `MGMT, DEV, westeurope`"""
    return {"messages": [("assistant", q)]}

def parse_environment(state: AgentState):
    last = state["messages"][-1][1]
    try:
        d, w, r = [p.strip() for p in last.split(",")]
        # LLM-Validation
        resp = llm.invoke(f"Validate: deployer={d}, workload={w}, region={r}. Reply VALID/INVALID.")
        if "INVALID" in resp.upper():
            return {"messages": [("assistant", f"⚠️ {resp}")]}
        
        return {
            "user_answers": {**state["user_answers"], "deployer": d, "workload": w, "region": r},
            "messages": [("assistant", "✅ Environment validiert!")],
            "current_block": "sap_system"
        }
    except:
        return {"messages": [("assistant", "❌ Brauche 3 Werte mit Kommas.")]}

def ask_sap(state: AgentState):
    q = """🪛 **SAP System Block** - Gib kommagetrennt:
1. SAP SID (3 Zeichen, z.B. X01)
2. Produkt (S4HANA2023/S4HANA2022/SAP_NETWEAVER_750)
3. Sizing (small/medium/large)
**Beispiel**: `X01, S4HANA2023, small`"""
    return {"messages": [("assistant", q)]}

def parse_sap(state: AgentState):
    last = state["messages"][-1][1]
    try:
        sid, prod, size = [p.strip() for p in last.split(",")]
        resp = llm.invoke(f"Validate SAP SID '{sid}' (3 uppercase chars). Reply VALID/INVALID.")
        if "INVALID" in resp.upper():
            return {"messages": [("assistant", f"⚠️ {resp}")]}
        
        return {
            "user_answers": {**state["user_answers"], "sap_sid": sid.upper(), "product": prod, "sizing": size},
            "messages": [("assistant", "✅ SAP System validiert!\n🎉 **Alle Daten gesammelt - TFVARS wird generiert...**")],
            "current_block": "complete",
            "tfvars_ready": True
        }
    except:
        return {"messages": [("assistant", "❌ Brauche 3 Werte mit Kommas.")]}

def generate_tfvars(state: AgentState):
    try:
        from easy_mode_config import load_defaults, get_sizing_config
        defaults = load_defaults()
        defaults.update(state["user_answers"])
        
        # Ableitete Werte
        defaults["sap_system_name"] = state["user_answers"]["sap_sid"]
        defaults["database_sid"] = state["user_answers"]["sap_sid"] + "DB"
        defaults["workload_zone"] = f"{state['user_answers']['workload']}-WEEU-{state['user_answers']['sap_sid']}"
        defaults["sap_product_id"] = state["user_answers"]["product"]
        defaults["location"] = state["user_answers"]["region"]
        
        # Sizing
        sizing = get_sizing_config(state["user_answers"]["sizing"])
        defaults.update(sizing)
        
        # Render
        template = jinja_env.get_template("sap.tfvars.j2")
        tfvars = template.render(config=defaults)
        
        state["tfvars_content"] = tfvars  # Speichere für Frontend
        return state
    except Exception as e:
        logging.error(f"TFVARS Error: {e}")
        state["messages"].append(("assistant", f"❌ TFVARS-Fehler: {e}"))
        return state

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("ask_env", ask_environment)
workflow.add_node("parse_env", parse_environment)
workflow.add_node("ask_sap", ask_sap)
workflow.add_node("parse_sap", parse_sap)
workflow.add_node("gen_tfvars", generate_tfvars)

workflow.set_entry_point("ask_env")
workflow.add_edge("ask_env", "parse_env")
workflow.add_edge("parse_env", "ask_sap")
workflow.add_edge("ask_sap", "parse_sap")
workflow.add_edge("parse_sap", "gen_tfvars")
workflow.add_edge("gen_tfvars", END)

chat_agent = workflow.compile()

# FastAPI
class ChatRequest(BaseModel):
    message: str
    state: Dict[str, Any] = None

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        # Init state
        if not req.state:
            req.state = create_initial_state()
        
        # Run agent
        result = chat_agent.invoke(req.state)
        
        # Get last message
        last_msg = result["messages"][-1][1] if result["messages"] else "Keine Antwort"
        
        # Extract TFVARS if ready
        tfvars = getattr(result, "tfvars_content", "")
        
        return {
            "reply": last_msg,
            "state": result,
            "tfvars": tfvars,
            "tfvars_ready": result["tfvars_ready"]
        }
    except Exception as e:
        logging.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}