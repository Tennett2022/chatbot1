from typing import List, Dict
from app.llm.base_llm import BaseLLM
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLM):
    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
            )
        except ImportError:
            raise RuntimeError(
                "google-generativeai package not installed. Run: pip install google-generativeai"
            )

    def get_provider_name(self) -> str:
        return "gemini"

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        try:
            # Gemini uses a different format - combine system + conversation
            chat_history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

            chat = self.model.start_chat(history=chat_history)
            last_user_msg = messages[-1]["content"] if messages else ""
            full_prompt = (
                f"{system_prompt}\n\n{last_user_msg}" if not chat_history else last_user_msg
            )

            response = await chat.send_message_async(
                full_prompt,
                generation_config={"max_output_tokens": max_tokens, "temperature": temperature},
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
