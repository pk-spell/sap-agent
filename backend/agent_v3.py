"""
SAP Deployment Agent V3 - Mit LLM-Factory (austauschbar!)
==========================================================

Neuer Agent mit:
- LLM-Factory Integration (austauschbare LLMs!)
- Alle bestehenden Parser/Validators (UNVERÄNDERT!)
- Vereinfachter Code
- Bessere Fehlerbehandlung

Unterstützt:
- Ollama (lokal, kostenlos)
- Claude, GPT-4, Groq (später per config.yaml)
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from langchain.schema import HumanMessage, AIMessage, SystemMessage

# LLM Factory - austauschbar!
from config_loader import get_config

# Unsere bestehenden Parser & Validators (UNVERÄNDERT!)
from parsers.environment import parse_environment_input
from parsers.sap_system import parse_sap_system_input
from parsers.sizing import parse_sizing_input
from parsers.architecture import parse_architecture_input
from parsers.network import parse_network_input
from parsers.os_selection import parse_os_selection_input

from utils.validators import (
    validate_environment,
    validate_sap_system,
    validate_sizing,
    validate_architecture,
    validate_network,
    validate_os_selection
)

from tfvars.generator import generate_tfvars


class AgentState:
    """Agent State Management"""

    def __init__(self):
        self.messages: List[Tuple[str, str]] = []
        self.current_step = 0
        self.user_answers: Dict[str, Any] = {}
        self.tfvars_content: Optional[str] = None
        self.tfvars_ready = False

        # 6-Schritt Konversationsflow
        self.steps = [
            "environment",
            "sap_system",
            "sizing",
            "architecture",
            "network",
            "os_selection"
        ]

    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.messages.append((role, content))

    def get_current_step(self) -> str:
        """Get current step name"""
        if self.current_step >= len(self.steps):
            return "complete"
        return self.steps[self.current_step]

    def advance_step(self):
        """Move to next step"""
        self.current_step += 1

    def is_complete(self) -> bool:
        """Check if all steps are done"""
        return self.current_step >= len(self.steps)


class SAPAgent:
    """SAP Deployment Agent with LLM-Factory"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize agent with config"""
        self.config = get_config(config_path)

        # Get LLMs from config (austauschbar!)
        self.parsing_llm = self.config.get_llm("parsing")
        self.default_llm = self.config.get_llm("default")

        # Agent state
        self.state = AgentState()

        # Step-specific prompts
        self.step_prompts = {
            "environment": """Du hilfst beim Erstellen von SAP Deployment Konfigurationen.

Stelle jetzt Fragen zur **Umgebung**:
1. Deployer Name (z.B. "DEV-WEEU-DEP00")
2. Workload Zone Name (z.B. "DEV-WEEU-SAP01")
3. Azure Region (z.B. "westeurope", "germanywestcentral")

Sei freundlich und konversationell. Frage nach einem Punkt, warte auf Antwort.""",

            "sap_system": """Jetzt Fragen zum **SAP System**:
1. SAP SID (3 Zeichen, z.B. "S01", "P01")
2. SAP Produkt (HANA, S/4HANA, BW/4HANA, etc.)
3. Environment Type (dev, qa, prod)

Sei konversationell.""",

            "sizing": """Jetzt zur **Größe des Systems**:
1. VM Size (z.B. "Standard_E16ds_v4", "Standard_M32ls")
2. Disk Configuration (Storage Typ, Größe)
3. HANA Memory (z.B. "128 GB", "256 GB")

Nutze die HANA Sizing Guidelines.""",

            "architecture": """Zur **Architektur**:
1. High Availability? (Ja/Nein)
2. Deployment Type (Standalone, Distributed)
3. Weitere Komponenten?

Erkläre Optionen.""",

            "network": """**Netzwerk Konfiguration**:
1. VNet Address Space (z.B. "10.0.0.0/16")
2. Subnet Ranges
3. NSG Rules

Hilf bei Planung.""",

            "os_selection": """Zum Schluss das **Betriebssystem**:
1. OS Type (SLES, RHEL, Windows)
2. OS Version
3. License Type

Empfehle basierend auf SAP-Support."""
        }

    async def process_message(self, user_input: str) -> str:
        """
        Process user message and return response

        Args:
            user_input: User's message

        Returns:
            Agent's response
        """
        # Add user message to history
        self.state.add_message("user", user_input)

        # Get current step
        current_step = self.state.get_current_step()

        if current_step == "complete":
            return await self._handle_complete()

        # Parse user input for current step
        parsed_data = await self._parse_input(user_input, current_step)

        if parsed_data:
            # Validate parsed data
            is_valid, validation_msg = self._validate_data(parsed_data, current_step)

            if is_valid:
                # Store data
                self.state.user_answers[current_step] = parsed_data

                # Advance to next step
                self.state.advance_step()

                # Check if complete
                if self.state.is_complete():
                    return await self._generate_tfvars()

                # Ask next question
                response = await self._ask_next_question()
            else:
                # Invalid data, ask again
                response = f"{validation_msg}\n\nBitte gib die Informationen nochmal an."
        else:
            # Could not parse, ask for clarification
            response = await self._ask_clarification(user_input, current_step)

        self.state.add_message("assistant", response)
        return response

    async def _parse_input(self, user_input: str, step: str) -> Optional[Dict[str, Any]]:
        """Parse user input for current step"""

        # Use step-specific parser (UNVERÄNDERT aus v2!)
        parsers = {
            "environment": parse_environment_input,
            "sap_system": parse_sap_system_input,
            "sizing": parse_sizing_input,
            "architecture": parse_architecture_input,
            "network": parse_network_input,
            "os_selection": parse_os_selection_input
        }

        parser = parsers.get(step)
        if not parser:
            return None

        # Call parser with LLM
        try:
            result = parser(user_input, self.parsing_llm)
            return result
        except Exception as e:
            print(f"Parse error: {e}")
            return None

    def _validate_data(self, data: Dict[str, Any], step: str) -> Tuple[bool, str]:
        """Validate parsed data"""

        validators = {
            "environment": validate_environment,
            "sap_system": validate_sap_system,
            "sizing": validate_sizing,
            "architecture": validate_architecture,
            "network": validate_network,
            "os_selection": validate_os_selection
        }

        validator = validators.get(step)
        if not validator:
            return True, "OK"

        try:
            is_valid, msg = validator(data)
            return is_valid, msg
        except Exception as e:
            return False, f"Validation error: {e}"

    async def _ask_next_question(self) -> str:
        """Ask question for next step"""

        next_step = self.state.get_current_step()
        if next_step == "complete":
            return await self._generate_tfvars()

        # Get step-specific prompt
        system_prompt = self.step_prompts.get(next_step, "")

        # Build context from previous answers
        context = self._build_context()

        # Use LLM to generate friendly question
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context: {context}\n\nStelle jetzt die erste Frage zu diesem Schritt.")
        ]

        try:
            response = self.default_llm.invoke(messages)
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            # Fallback to template question
            return self._get_template_question(next_step)

    async def _ask_clarification(self, user_input: str, step: str) -> str:
        """Ask for clarification when input unclear"""

        system_prompt = f"""Der User hat etwas zu {step} gesagt, aber es war unklar.

Frage höflich nach den fehlenden Informationen."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f'User sagte: "{user_input}"\n\nWas sollten wir nachfragen?')
        ]

        try:
            response = self.default_llm.invoke(messages)
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            return "Ich habe das nicht ganz verstanden. Kannst du das nochmal sagen?"

    def _build_context(self) -> str:
        """Build context string from collected data"""
        context_parts = []
        for step, data in self.state.user_answers.items():
            context_parts.append(f"{step}: {json.dumps(data)}")
        return "\n".join(context_parts)

    def _get_template_question(self, step: str) -> str:
        """Fallback template questions"""
        templates = {
            "environment": "Lass uns mit der Umgebung starten. Wie soll der Deployer heißen? (z.B. DEV-WEEU-DEP00)",
            "sap_system": "Jetzt zum SAP System. Welche SAP SID möchtest du verwenden? (3 Zeichen, z.B. S01)",
            "sizing": "Zur Größe: Welche VM Size brauchst du? (z.B. Standard_E16ds_v4)",
            "architecture": "Zur Architektur: Brauchst du High Availability? (Ja/Nein)",
            "network": "Zum Netzwerk: Welcher VNet Address Space? (z.B. 10.0.0.0/16)",
            "os_selection": "Zum Schluss: Welches OS? (SLES, RHEL, Windows)"
        }
        return templates.get(step, "Was möchtest du konfigurieren?")

    async def _generate_tfvars(self) -> str:
        """Generate TFVARS file from collected data"""

        try:
            # Use existing generator (UNVERÄNDERT!)
            tfvars_content = generate_tfvars(self.state.user_answers)

            self.state.tfvars_content = tfvars_content
            self.state.tfvars_ready = True

            return f"""Perfekt! Ich habe alle Informationen.

Deine TFVARS Datei ist fertig! 🎉

Du kannst sie jetzt herunterladen oder in der Vorschau anzeigen.

Möchtest du noch etwas ändern?"""

        except Exception as e:
            return f"Fehler beim Generieren der TFVARS: {e}"

    async def _handle_complete(self) -> str:
        """Handle messages after completion"""
        # Agent can answer questions about the generated config
        return "Die Konfiguration ist fertig. Möchtest du etwas ändern oder hast du Fragen?"

    def get_tfvars(self) -> Optional[str]:
        """Get generated TFVARS content"""
        return self.state.tfvars_content

    def reset(self):
        """Reset agent state"""
        self.state = AgentState()


# Singleton instance (per session in FastAPI)
_agent_instances: Dict[str, SAPAgent] = {}


def get_agent(session_id: str) -> SAPAgent:
    """Get or create agent instance for session"""
    if session_id not in _agent_instances:
        _agent_instances[session_id] = SAPAgent()
    return _agent_instances[session_id]


def reset_agent(session_id: str):
    """Reset agent for session"""
    if session_id in _agent_instances:
        _agent_instances[session_id].reset()


if __name__ == "__main__":
    # Test agent locally
    import asyncio

    async def test():
        agent = SAPAgent()

        # Test message
        response = await agent.process_message("Ich möchte ein SAP System in West Europe deployen")
        print(f"Agent: {response}")

    asyncio.run(test())
