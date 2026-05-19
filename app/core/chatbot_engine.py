from typing import Dict, List, Optional
from dataclasses import dataclass, field
from app.core.intent_classifier import classify_intent
from app.core.lead_extractor import extract_lead_data, get_missing_lead_fields
from app.core.escalation import should_escalate, get_escalation_response
from app.core.response_guardrails import check_response
from app.core.prompt_builder import build_system_prompt, build_conversation_messages
from app.llm import get_llm_provider
from app.utils.logger import get_logger
from app.utils.text import clean_text, truncate

logger = get_logger(__name__)


@dataclass
class EngineResponse:
    response: str
    intent: str
    confidence: float
    should_escalate: bool
    lead_data: Dict
    next_action: str  # "continue" | "capture_lead" | "escalate" | "farewell"
    metadata: Optional[Dict] = None


async def process_message(
    user_message: str,
    user_id: str,
    channel: str,
    history: List[Dict],
    lead_data: Optional[Dict] = None,
    message_count: int = 0,
) -> EngineResponse:
    """
    Core chatbot engine: processes a user message and returns a structured response.

    Args:
        user_message: The raw text from the user.
        user_id: Unique user identifier (from the channel).
        channel: Source channel (telegram | whatsapp | web).
        history: Recent conversation history (list of {message_in, message_out}).
        lead_data: Known lead information for this user.
        message_count: Total messages in this conversation.

    Returns:
        EngineResponse with all relevant fields.
    """
    lead_data = lead_data or {}
    cleaned_message = clean_text(user_message)

    # 1. Classify intent
    intent, confidence = classify_intent(cleaned_message)
    logger.info(f"[{channel}] user={user_id} intent={intent} confidence={confidence:.2f}")

    # 2. Extract lead data from this message
    new_lead_fields = extract_lead_data(cleaned_message, existing=lead_data)
    merged_lead = {**lead_data, **new_lead_fields}

    # 3. Check escalation
    escalate = should_escalate(intent, cleaned_message, merged_lead, message_count)

    if escalate:
        escalation_response = get_escalation_response(merged_lead)
        if merged_lead.get("email") or merged_lead.get("telefono"):
            merged_lead["estado"] = "pendiente_contacto"
        return EngineResponse(
            response=escalation_response,
            intent=intent,
            confidence=confidence,
            should_escalate=True,
            lead_data=merged_lead,
            next_action="escalate",
        )

    # 4. Build LLM prompt and conversation
    system_prompt = build_system_prompt(lead_data=merged_lead)
    conversation_messages = build_conversation_messages(history)

    # Add current message
    conversation_messages.append({"role": "user", "content": cleaned_message})

    # 5. Generate LLM response
    try:
        llm = get_llm_provider()
        raw_response = await llm.generate_response(
            system_prompt=system_prompt,
            messages=conversation_messages,
            max_tokens=600,
            temperature=0.7,
        )
    except Exception as e:
        logger.error(f"LLM error for user={user_id}: {e}")
        raw_response = (
            "En este momento tengo un inconveniente técnico. "
            "Por favor intenta nuevamente en un momento, o puedo derivarte con el equipo de Crovenett."
        )

    # 6. Apply guardrails
    safe_response = check_response(raw_response, intent)
    final_response = truncate(safe_response, 4000)

    # 7. Determine next action
    missing_fields = get_missing_lead_fields(merged_lead)
    if intent == "despedida":
        next_action = "farewell"
    elif len(missing_fields) > 0 and intent in {"cliente_interesado", "precios", "agendar_reunion"}:
        next_action = "capture_lead"
    else:
        next_action = "continue"

    return EngineResponse(
        response=final_response,
        intent=intent,
        confidence=confidence,
        should_escalate=False,
        lead_data=merged_lead,
        next_action=next_action,
        metadata={"missing_lead_fields": missing_fields},
    )
