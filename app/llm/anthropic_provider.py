from typing import List, Dict
from app.llm.base_llm import BaseLLM
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLM):
    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = settings.ANTHROPIC_MODEL
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    def get_provider_name(self) -> str:
        return "anthropic"

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
