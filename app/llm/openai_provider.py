from typing import List, Dict
from app.llm.base_llm import BaseLLM
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLM):
    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    def get_provider_name(self) -> str:
        return "openai"

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
