"""
Session Model
=============

ChatSession class for managing conversation state.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ChatSession:
    """Represents a chat session with state and conversation history"""

    session_id: str
    current_prompt: int = 0
    user_data: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, str]] = field(default_factory=list)
    tfvars_ready: bool = False
    tfvars_content: str = ""

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})

    def get_title(self) -> str:
        """Generate a session title from the first user message or user_data"""
        # Try to get from user_data first
        if "environment" in self.user_data and "location" in self.user_data:
            env = self.user_data.get("environment", "")
            location = self.user_data.get("location", "")
            sid = self.user_data.get("sid", "")
            if sid:
                return f"{env} - {sid} ({location})"
            return f"{env} - {location}"

        # Fallback: use first user message
        for msg in self.messages:
            if msg["role"] == "user":
                title = msg["content"][:50]
                if len(msg["content"]) > 50:
                    title += "..."
                return title

        return "New Chat"
