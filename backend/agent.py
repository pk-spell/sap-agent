from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    tfvars_config: dict  # Alle gesammelten Parameter
    current_block: str   # Welcher Block wird gerade gefüllt?
    mode: str           # "easy" oder "advanced"
    missing_fields: list # Was fehlt noch?

llm = OllamaLLM(model="llama3.1:8b", base_url="http://host.docker.internal:11434")

# Easy Mode Defaults aus Datei
EASY_DEFAULTS = {
    "location": "westeurope",
    "database_platform": "HANA",
    "app_tier_sku": "Standard_D2s_v3",
    "database_tier_sku": "Standard_E4s_v3",
    "high_availability": False,
    "automation_username": "azureadm",
    # ... alle anderen Standardwerte
}

# LangGraph Definition
def ask_environment_block(state: AgentState):
    """Fragt nach Environment-Block (1-2 Fragen)"""
    if state["current_block"] != "environment":
        return {"current_block": "environment"}
    
    # Batch-Frage: 3 Dinge auf einmal
    question = """
    Gebe die folgenden Umgebungswerte an (kommagetrennt):
    - Deployer Environment (z.B. MGMT, DEV)
    - Workload Environment (z.B. DEV, TST, PRD) 
    - Workload Zone (z.B. DEV-WEEU)
    Beispiel: DEV, DEV, DEV-WEEU
    """
    
    return {"messages": [("assistant", question)]}

def parse_environment_block(state: AgentState):
    """Parst die Antwort und füllt TFVARS"""
    last_msg = state["messages"][-1][1]  # User-Antwort
    
    # Einfacher Parser für Batch-Antwort
    parts = [p.strip() for p in last_msg.split(",")]
    if len(parts) == 3:
        return {
            "tfvars_config": {
                **state["tfvars_config"],
                "deployer_environment": parts[0],
                "workload_environment": parts[1],
                "workload_zone": parts[2],
            },
            "current_block": "sap_system"  # Nächster Block
        }
    
    return {"messages": [("assistant", "Bitte genau 3 Werte mit Kommas angeben.")]}

# Baue den Graph
workflow = StateGraph(AgentState)

# Knoten hinzufügen (jeder Block = 2 Knoten: ask + parse)
workflow.add_node("ask_env", ask_environment_block)
workflow.add_node("parse_env", parse_environment_block)
workflow.add_node("ask_sap", ask_sap_block)
workflow.add_node("parse_sap", parse_sap_block)
# ... für jeden Block

# Startknoten
workflow.set_entry_point("ask_env")

# Bedingte Übergänge
workflow.add_edge("ask_env", "parse_env")
workflow.add_conditional_edges("parse_env", decide_next_block)

# Kompilieren
app = workflow.compile()