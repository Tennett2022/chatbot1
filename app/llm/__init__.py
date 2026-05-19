from app.llm.base_llm import BaseLLM
from app.config import settings


def get_llm_provider() -> BaseLLM:
    """Factory: returns the configured LLM provider instance."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    elif provider == "gemini":
        from app.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. Options: openai | anthropic | gemini"
        )
