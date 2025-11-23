"""
LLM Factory - Austauschbare LLM-Integration
============================================

Unterstützt:
- Ollama (lokal, kostenlos)
- Claude (Anthropic API)
- GPT-4 (OpenAI API)
- Azure OpenAI
- Groq (schnell & billig)
- Weitere...

Usage:
    from llm_factory import get_llm

    # Lokal
    llm = get_llm("ollama", model="qwen2.5:7b")

    # Claude
    llm = get_llm("claude", model="claude-3-5-sonnet-20241022", api_key="...")

    # GPT-4
    llm = get_llm("openai", model="gpt-4-turbo", api_key="...")
"""

import os
from typing import Optional, Dict, Any
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"


class LLMConfig:
    """LLM Configuration"""

    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs


def get_llm(
    provider: str = "ollama",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs
):
    """
    Factory function to get LLM instance

    Args:
        provider: LLM provider (ollama, claude, openai, azure_openai, groq)
        model: Model name/ID
        api_key: API key (optional, reads from env)
        base_url: Custom base URL (optional)
        temperature: Sampling temperature (0.0 - 1.0)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional provider-specific parameters

    Returns:
        LangChain LLM instance

    Examples:
        >>> # Ollama (lokal)
        >>> llm = get_llm("ollama", model="qwen2.5:7b")

        >>> # Claude API
        >>> llm = get_llm("claude", model="claude-3-5-sonnet-20241022", api_key="sk-...")

        >>> # OpenAI GPT-4
        >>> llm = get_llm("openai", model="gpt-4-turbo", api_key="sk-...")

        >>> # Groq (schnell & billig)
        >>> llm = get_llm("groq", model="llama-3.1-70b-versatile", api_key="gsk_...")
    """

    provider = LLMProvider(provider.lower())

    # Default models
    default_models = {
        LLMProvider.OLLAMA: "qwen2.5:7b",
        LLMProvider.CLAUDE: "claude-3-5-sonnet-20241022",
        LLMProvider.OPENAI: "gpt-4-turbo",
        LLMProvider.AZURE_OPENAI: "gpt-4",
        LLMProvider.GROQ: "llama-3.1-70b-versatile",
    }

    model = model or default_models.get(provider)

    # Import LangChain components dynamically
    try:
        if provider == LLMProvider.OLLAMA:
            from langchain_ollama import OllamaLLM

            return OllamaLLM(
                model=model,
                base_url=base_url or "http://localhost:11434",
                temperature=temperature,
                num_predict=max_tokens,
                **kwargs
            )

        elif provider == LLMProvider.CLAUDE:
            from langchain_anthropic import ChatAnthropic

            if not api_key:
                raise ValueError("Claude API key required (set CLAUDE_API_KEY env var)")

            return ChatAnthropic(
                model=model,
                anthropic_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        elif provider == LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI

            if not api_key:
                raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")

            return ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        elif provider == LLMProvider.AZURE_OPENAI:
            from langchain_openai import AzureChatOpenAI

            if not api_key:
                raise ValueError("Azure OpenAI API key required")

            azure_endpoint = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
            if not azure_endpoint:
                raise ValueError("Azure OpenAI endpoint required")

            return AzureChatOpenAI(
                deployment_name=model,
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        elif provider == LLMProvider.GROQ:
            from langchain_groq import ChatGroq

            if not api_key:
                raise ValueError("Groq API key required (set GROQ_API_KEY env var)")

            return ChatGroq(
                model=model,
                groq_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    except ImportError as e:
        raise ImportError(
            f"Missing dependency for {provider}. Install with:\n"
            f"pip install langchain-{provider.value}"
        ) from e


def get_multi_llm_config() -> Dict[str, Any]:
    """
    Get multi-LLM configuration for different tasks

    Example strategy:
    - Parsing: Fast local model (qwen2.5:7b)
    - Validation: Precise model (Claude)
    - Generation: Best quality model (GPT-4)

    Returns:
        Dict with LLM instances for different tasks
    """

    return {
        "parsing": get_llm("ollama", model="qwen2.5:7b", temperature=0.3),
        "validation": get_llm("ollama", model="qwen2.5:7b", temperature=0.1),
        "generation": get_llm("ollama", model="llama3.1:8b", temperature=0.5),
        "default": get_llm("ollama", model="qwen2.5:7b", temperature=0.7),
    }


# Convenience functions
def get_ollama_llm(model: str = "qwen2.5:7b", **kwargs):
    """Get Ollama LLM (local)"""
    return get_llm("ollama", model=model, **kwargs)


def get_claude_llm(model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None, **kwargs):
    """Get Claude LLM (Anthropic API)"""
    return get_llm("claude", model=model, api_key=api_key, **kwargs)


def get_openai_llm(model: str = "gpt-4-turbo", api_key: Optional[str] = None, **kwargs):
    """Get OpenAI LLM"""
    return get_llm("openai", model=model, api_key=api_key, **kwargs)


def get_groq_llm(model: str = "llama-3.1-70b-versatile", api_key: Optional[str] = None, **kwargs):
    """Get Groq LLM (fast & cheap)"""
    return get_llm("groq", model=model, api_key=api_key, **kwargs)


if __name__ == "__main__":
    # Test local Ollama
    print("Testing Ollama...")
    llm = get_ollama_llm()
    response = llm.invoke("Erkläre SAP HANA in einem Satz.")
    print(f"Response: {response}")

    print("\nAvailable providers:")
    for provider in LLMProvider:
        print(f"  - {provider.value}")
