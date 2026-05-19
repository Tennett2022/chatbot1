from app.utils.logger import get_logger

logger = get_logger(__name__)

ESCALATION_TRIGGERS_INTENTS = {
    "soporte_humano",
    "agendar_reunion",
    "cliente_interesado",
}

ESCALATION_TRIGGER_PHRASES = [
    "hablar con alguien",
    "hablar con una persona",
    "hablar con un humano",
    "hablar con un ejecutivo",
    "quiero que me contacten",
    "quiero que me llamen",
    "precio exacto",
    "precio definitivo",
    "contrato",
    "contratar",
    "queja",
    "reclamo",
    "problema",
    "no funciona",
]


def should_escalate(
    intent: str,
    text: str,
    lead_data: dict,
    message_count: int = 0,
) -> bool:
    """
    Determine if this conversation should be escalated to a human agent.

    Escalation triggers:
    - Intent is in escalation set
    - User explicitly asks for a person
    - User has commercial intent + contact data
    - User asks for exact pricing
    - Sensitive complaint
    """
    normalized = text.lower()

    # Intent-based escalation
    if intent in ESCALATION_TRIGGERS_INTENTS:
        logger.info(f"Escalation triggered by intent: {intent}")
        return True

    # Phrase-based escalation
    for phrase in ESCALATION_TRIGGER_PHRASES:
        if phrase in normalized:
            logger.info(f"Escalation triggered by phrase: '{phrase}'")
            return True

    # Lead data + commercial intent → escalate after enough context
    has_contact = lead_data.get("email") or lead_data.get("telefono")
    has_company = lead_data.get("empresa")
    if has_contact and has_company and message_count >= 3:
        logger.info("Escalation triggered: lead has contact data and company after conversation")
        return True

    return False


def get_escalation_response(lead_data: dict) -> str:
    """Return appropriate escalation message based on what data we have."""
    has_name = lead_data.get("nombre")
    has_email = lead_data.get("email")
    has_phone = lead_data.get("telefono")
    has_company = lead_data.get("empresa")

    missing = []
    if not has_name:
        missing.append("tu nombre")
    if not has_company:
        missing.append("el nombre de tu empresa")
    if not has_email and not has_phone:
        missing.append("un correo o teléfono de contacto")

    if missing:
        missing_str = ", ".join(missing)
        return (
            f"Perfecto, con gusto te conecto con el equipo de Crovenett. "
            f"Para poder derivar tu solicitud, necesito que me indiques {missing_str}. "
            f"¿Me los puedes compartir?"
        )
    else:
        contact = has_email or has_phone
        return (
            f"Excelente, {has_name or 'te'} derivaré con el equipo de Crovenett. "
            f"Alguien se pondrá en contacto contigo a la brevedad a través de {contact}. "
            f"¡Gracias por tu interés!"
        )
