"""
Configuration Loader
Lädt config.yaml und erstellt LLM-Instanzen
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from llm_factory import get_llm


class Config:
    """Application configuration"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML config file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        # Expand environment variables
        config = self._expand_env_vars(config)
        return config

    def _expand_env_vars(self, obj):
        """Recursively expand ${VAR} in config"""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj

    def get_llm(self, task: str = "default"):
        """
        Get LLM instance for specific task

        Args:
            task: Task name (default, parsing, validation, generation)

        Returns:
            LangChain LLM instance
        """
        llm_config = self._config.get("llm", {})

        # Check if task-specific LLM exists
        task_config = llm_config.get("tasks", {}).get(task)
        if task_config:
            config = task_config
        else:
            # Fall back to default
            config = llm_config.get("default", {})

        provider = config.get("provider", "ollama")
        model = config.get("model")
        api_key = config.get("api_key")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)

        return get_llm(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self._config.get("server", {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": True
        })

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self._config.get("database", {
            "type": "sqlite",
            "path": "data/chat_history.db"
        })

    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return self._config.get("cors", {
            "origins": ["http://localhost:5173"],
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        })


# Global config instance
_config = None


def get_config(config_path: str = "config.yaml") -> Config:
    """Get global config instance (singleton)"""
    global _config
    if _config is None:
        # Try to find config in backend directory
        backend_dir = Path(__file__).parent
        config_file = backend_dir / config_path

        if not config_file.exists():
            # Try current directory
            config_file = Path(config_path)

        _config = Config(str(config_file))
    return _config


if __name__ == "__main__":
    # Test config loading
    config = get_config()

    print("Server Config:")
    print(config.get_server_config())

    print("\nDatabase Config:")
    print(config.get_database_config())

    print("\nTesting LLMs:")
    print(f"Default LLM: {config.get_llm('default')}")
    print(f"Parsing LLM: {config.get_llm('parsing')}")
    print(f"Validation LLM: {config.get_llm('validation')}")
    print(f"Generation LLM: {config.get_llm('generation')}")
