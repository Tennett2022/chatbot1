from abc import ABC, abstractmethod
from typing import List, Dict


class BaseLLM(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: The system instructions for the model.
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0=deterministic, 1=creative).

        Returns:
            The model's text response.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass
