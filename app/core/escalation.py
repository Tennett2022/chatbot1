from app.utils.logger import get_logger

logger = get_logger(__name__)

# Intents that ALWAYS trigger escalation
ESCALATION_INTENTS = {
    "soporte_humano",
    "agendar_reunion",
}

# Intents that trigger escalation only when lead has contact data
SOFT_ESCALATION_INTENTS = {
    "cliente_interesado",
}

# Exact phrases that trigger escalation (case-insensitive substring match)
# NOTE: Keep these specific to avoid false positives.
# "problema" alone is too broad — use "tengo un problema con" or "queja" instead.
ESCALATION_PHRASES = [
    "hablar con alguien",
    "hablar con una persona",
    "hablar con un humano",
    "hablar con un ejecutivo",
    "hablar con un asesor",
    "quiero que me llamen",
    "quiero que me contacten",
    "necesito que me contacten",
    "precio exacto",
    "precio definitivo",
    "quiero contratar",
    "quisiera contratar",
    "cómo contrato",
    "cómo empezamos",
    "quiero hacer una queja",
    "quiero hacer un reclamo",
    "tengo una queja",
    "tengo un reclamo",
]

# Minimum conversation turns before auto-escalating a complete lead
_MIN_TURNS_FOR_AUTO_ESCALATION = 5


def should_escalate(
    intent: str,
    text: str,
    lead_data: dict,
    message_count: int = 0,
) -> bool:
    """
    Determine whether this turn should be handed off to a human agent.

    Escalation logic (evaluated in priority order):
    1. Hard intent trigger (soporte_humano, agendar_reunion).
    2. Explicit escalation phrase in message.
    3. Soft intent (cliente_interesado) + has contact data.
    4. Lead is complete (name + company + contact) after a meaningful conversation.

    Args:
        intent:        Detected intent for this message.
        text:          Raw user message (lowercased internally).
        lead_data:     Accumulated lead fields for this user.
        message_count: Number of completed turns so far.

    Returns:
        True if the conversation should be escalated, False otherwise.
    """
    normalized = text.lower()

    # 1. Hard intent escalation
    if intent in ESCALATION_INTENTS:
        logger.info(f"Escalation: hard intent trigger '{intent}'")
        return True

    # 2. Explicit phrase escalation
    for phrase in ESCALATION_PHRASES:
        if phrase in normalized:
            logger.info(f"Escalation: phrase trigger '{phrase}'")
            return True

    # 3. Soft intent + already has contact info
    has_contact = bool(lead_data.get("email") or lead_data.get("telefono"))
    if intent in SOFT_ESCALATION_INTENTS and has_contact:
        logger.info(f"Escalation: soft intent '{intent}' with contact data")
        return True

    # 4. Lead is complete after meaningful conversation
    has_name = bool(lead_data.get("nombre"))
    has_company = bool(lead_data.get("empresa"))
    if has_name and has_company and has_contact and message_count >= _MIN_TURNS_FOR_AUTO_ESCALATION:
        logger.info("Escalation: complete lead after full conversation")
        return True

    return False


def get_escalation_response(lead_data: dict) -> str:
    """
    Build the escalation message.
    If data is missing, ask for it. If complete, confirm the handoff.
    """
    nombre = lead_data.get("nombre")
    empresa = lead_data.get("empresa")
    email = lead_data.get("email")
    telefono = lead_data.get("telefono")

    missing: list[str] = []
    if not nombre:
        missing.append("tu nombre")
    if not empresa:
        missing.append("tu empresa")
    if not email and not telefono:
        missing.append("un correo o teléfono de contacto")

    if missing:
        missing_str = ", ".join(missing)
        return (
            f"Con gusto te conecto con el equipo de Crovenett. "
            f"Para derivar tu solicitud necesito que me indiques {missing_str}. "
            f"¿Me los puedes compartir?"
        )

    contacto = email or telefono
    saludo = f"Perfecto, {nombre}" if nombre else "Perfecto"
    return (
        f"{saludo}. Le paso tus datos al equipo de Crovenett y te contactarán "
        f"a la brevedad a través de {contacto}. "
        f"¡Gracias por tu interés en Crovenett!"
    )
