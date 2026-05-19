"""
Chatbot Engine — the core processing pipeline.

Separation of concerns:
  Channel layer  →  parses/sends messages (telegram_channel, whatsapp_channel)
  Engine layer   →  classifies, extracts, escalates, calls LLM, applies guardrails
  Storage layer  →  persists conversations and leads

The engine knows nothing about Telegram or WhatsApp. It receives normalized
text and returns a structured EngineResponse.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.escalation import get_escalation_response, should_escalate
from app.core.intent_classifier import classify_intent
from app.core.lead_extractor import extract_lead_data, get_missing_lead_fields
from app.core.prompt_builder import build_conversation_messages, build_system_prompt
from app.core.response_guardrails import (
    check_response,
    is_out_of_scope,
    scope_redirect_response,
)
from app.llm import get_llm_provider
from app.llm.base_llm import BaseLLM
from app.utils.logger import get_logger
from app.utils.text import clean_text, truncate

logger = get_logger(__name__)

# Cache LLM provider — instantiated once per process, not per request.
# If LLM_PROVIDER changes at runtime, restart the server.
_llm_provider: Optional[BaseLLM] = None


def _get_cached_llm() -> BaseLLM:
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = get_llm_provider()
        logger.info(f"LLM provider initialized: {_llm_provider.get_provider_name()}")
    return _llm_provider


@dataclass
class EngineResponse:
    """Structured result for every processed message."""
    response: str
    intent: str
    confidence: float
    should_escalate: bool
    lead_data: Dict
    next_action: str  # "continue" | "capture_lead" | "escalate" | "farewell"
    metadata: Dict = field(default_factory=dict)


async def process_message(
    user_message: str,
    user_id: str,
    channel: str,
    history: List[Dict],
    lead_data: Optional[Dict] = None,
    message_count: int = 0,
) -> EngineResponse:
    """
    Process a single user message through the full chatbot pipeline.

    Pipeline:
      1. Sanitize input
      2. Classify intent
      3. Extract new lead fields (non-destructive: won't overwrite existing data)
      4. Check escalation conditions (before LLM to save tokens when escalating)
      5. Build system prompt (with cached knowledge base)
      6. Generate LLM response (with timing log)
      7. Apply safety guardrails
      8. Determine next action

    Args:
        user_message:  Raw text from the user.
        user_id:       Channel-specific user identifier.
        channel:       Source channel name ("telegram" | "whatsapp" | "web").
        history:       Last N conversation turns [{message_in, message_out}].
        lead_data:     Accumulated lead fields from previous turns.
        message_count: Number of completed turns in this conversation.

    Returns:
        EngineResponse — never raises; errors produce a safe fallback response.
    """
    lead_data = lead_data or {}
    t_start = time.perf_counter()

    # 1. Sanitize
    cleaned = clean_text(user_message)
    if not cleaned:
        return EngineResponse(
            response="No recibí ningún mensaje. ¿En qué te puedo ayudar?",
            intent="fuera_de_alcance",
            confidence=0.0,
            should_escalate=False,
            lead_data=lead_data,
            next_action="continue",
        )

    # 2. Out-of-scope pre-check (avoids LLM call for clearly off-topic messages)
    if is_out_of_scope(cleaned):
        logger.info(f"scope_blocked channel={channel} user={user_id} msg_len={len(cleaned)}")
        return EngineResponse(
            response=scope_redirect_response(),
            intent="fuera_de_alcance",
            confidence=1.0,
            should_escalate=False,
            lead_data=lead_data,
            next_action="continue",
        )

    # 3. Intent classification
    intent, confidence = classify_intent(cleaned)
    logger.info(
        f"intent channel={channel} user={user_id} intent={intent} "
        f"conf={confidence:.2f} msg_len={len(cleaned)}"
    )

    # 4. Lead extraction (pass existing data so extractor skips already-known fields)
    new_fields = extract_lead_data(cleaned, existing=lead_data)
    # Merge: existing values are preserved; new fields fill the gaps
    merged_lead = {**lead_data, **{k: v for k, v in new_fields.items() if v is not None}}

    # 5. Escalation check (short-circuit before LLM)
    if should_escalate(intent, cleaned, merged_lead, message_count):
        escalation_text = get_escalation_response(merged_lead)
        # Mark lead as pending contact if we already have contact info
        if merged_lead.get("email") or merged_lead.get("telefono"):
            merged_lead["estado"] = "pendiente_contacto"
        logger.info(f"escalation channel={channel} user={user_id} intent={intent}")
        return EngineResponse(
            response=escalation_text,
            intent=intent,
            confidence=confidence,
            should_escalate=True,
            lead_data=merged_lead,
            next_action="escalate",
            metadata={"escalation_intent": intent},
        )

    # 6. Build LLM context
    system_prompt = build_system_prompt(lead_data=merged_lead)
    conv_messages = build_conversation_messages(history)
    conv_messages.append({"role": "user", "content": cleaned})

    # 7. LLM generation
    llm_error: Optional[str] = None
    t_llm = time.perf_counter()
    try:
        llm = _get_cached_llm()
        raw_response = await llm.generate_response(
            system_prompt=system_prompt,
            messages=conv_messages,
            max_tokens=600,
            temperature=0.7,
        )
        logger.info(
            f"llm_call provider={llm.get_provider_name()} "
            f"elapsed_ms={int((time.perf_counter() - t_llm) * 1000)} "
            f"user={user_id}"
        )
    except Exception as exc:
        logger.error(
            f"llm_error channel={channel} user={user_id} error={exc!r}",
            exc_info=True,
        )
        llm_error = str(exc)
        raw_response = (
            "Tuve un inconveniente técnico en este momento. "
            "Puedes intentar de nuevo, o si prefieres te conecto con el equipo de Crovenett."
        )

    # 8. Guardrails
    safe_response = check_response(raw_response, intent)
    final_response = truncate(safe_response, 4000)

    # 9. Next action
    missing = get_missing_lead_fields(merged_lead)
    if intent == "despedida":
        next_action = "farewell"
    elif missing and intent in {"cliente_interesado", "precios", "agendar_reunion"}:
        next_action = "capture_lead"
    else:
        next_action = "continue"

    total_ms = int((time.perf_counter() - t_start) * 1000)
    logger.info(
        f"engine_done channel={channel} user={user_id} "
        f"action={next_action} total_ms={total_ms}"
    )

    return EngineResponse(
        response=final_response,
        intent=intent,
        confidence=confidence,
        should_escalate=False,
        lead_data=merged_lead,
        next_action=next_action,
        metadata={
            "missing_lead_fields": missing,
            "llm_error": llm_error,
            "total_ms": total_ms,
        },
    )
