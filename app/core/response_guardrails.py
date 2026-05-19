import re
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Redirect message used when the bot goes off-scope ────────────────────────
_SCOPE_REDIRECT = (
    "Puedo ayudarte solo con información sobre Crovenett, sus soluciones de "
    "inteligencia artificial, automatización, chatbots, voicebots, integraciones "
    "y servicios comerciales. Si quieres, puedo contarte qué soluciones ofrecemos "
    "o ayudarte a identificar cuál podría servirle a tu empresa."
)

# ── Regex patterns that should NEVER appear in a bot response ─────────────────
# Each tuple is (pattern, reason_label)
FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    # Exact price quotes (number after price word)
    (r'\b(cuesta|vale|cobro|cobr[ao]mos|precio\s+(?:es|ser[aá]))\s+\$?\s*\d[\d.,]*\b', "exact_price"),
    # Fabricated guarantees
    (r'\bgarantiz(amos|o)\s+(?:que|el\s+resultado|el\s+[eé]xito|retorno)', "fake_guarantee"),
    # False superlatives about the company
    (r'\b(somos|soy)\s+(?:los?\s+)?(?:mejores?|l[ií]deres?|n[uú]mero\s+1|n[uú]mero\s+uno)\s+(?:del|en\s+el)', "superlative"),
    # Hallucinated well-known clients
    (r'\b(Amazon|Google|Apple|Microsoft|Meta|Tesla|Netflix)\s+(es|son|fue|ha\s+sido)\s+(cliente|nuestro)', "fake_client"),
    # Fabricated certifications
    (r'\bcertificad[ao]s?\s+(?:por|de)\s+(ISO|Google|Microsoft|AWS|Meta)\b', "fake_cert"),
    # Inventing specific integration names as confirmed
    (r'\btenemos\s+integración\s+nativa\s+con\b', "invented_native_integration"),
]

# ── Keyword-only price invention check ───────────────────────────────────────
PRICE_INVENTION_KEYWORDS: list[str] = [
    "precio fijo de $",
    "tarifa fija de $",
    "cuesta exactamente $",
    "cobraremos exactamente",
    "vale exactamente $",
    "inversión de $",
]

# ── Out-of-scope topic detection ──────────────────────────────────────────────
# Used both to catch off-scope LLM responses and to short-circuit clearly
# off-topic user messages before calling the LLM.
# Tuple: (keyword_in_lowercase, category_label)
OUT_OF_SCOPE_TOPICS: list[tuple[str, str]] = [
    # Politics
    ("partido político", "politics"),
    ("candidato político", "politics"),
    ("elecciones presidenciales", "politics"),
    ("gobierno de", "politics"),
    # Health / medicine
    ("asesoría médica", "medical"),
    ("diagnóstico médico", "medical"),
    ("receta médica", "medical"),
    ("tratamiento médico", "medical"),
    ("síntomas de", "medical"),
    ("hazme una dieta", "medical"),
    ("plan de dieta", "medical"),
    # Legal
    ("asesoría legal", "legal"),
    ("asesoría jurídica", "legal"),
    ("consejo legal", "legal"),
    ("demanda judicial", "legal"),
    # Finance / investments
    ("inversiones en bolsa", "finance"),
    ("comprar acciones", "finance"),
    ("criptomonedas como inversión", "finance"),
    ("fondos de inversión", "finance"),
    # Generic programming / tutorials
    ("explícame python", "generic_tech"),
    ("explícame javascript", "generic_tech"),
    ("cómo programar en", "generic_tech"),
    ("tutorial de programación", "generic_tech"),
    # School / homework
    ("tarea escolar", "homework"),
    ("ayúdame con la tarea", "homework"),
    ("resumen del libro", "homework"),
    # Entertainment / culture
    ("quién ganó las elecciones", "off_topic"),
    ("recomiéndame una película", "off_topic"),
    ("recomiéndame un restaurante", "off_topic"),
]

# ── User-message pre-check ────────────────────────────────────────────────────
# Patterns that unambiguously indicate a fully off-topic message.
# Only triggers when there is NO Crovenett-related keyword alongside.
_CROVENETT_SIGNALS = re.compile(
    r'\b(chatbot|bot|whatsapp|telegram|automatiz|crovenett|ia|inteligencia\s*artificial|'
    r'crm|integraci[oó]n|precio|costo|servicio|solución|lead|ventas|asesor|agente|'
    r'voicebot|dashboard|reporte|api)\b',
    re.IGNORECASE,
)


def is_out_of_scope(user_message: str) -> bool:
    """
    Return True when the user message is ENTIRELY off-topic (no Crovenett signal).
    Mixed messages (off-topic + Crovenett) return False — the LLM handles those.
    """
    lower = user_message.lower()
    has_scope_signal = bool(_CROVENETT_SIGNALS.search(user_message))
    if has_scope_signal:
        return False  # mixed question — let the LLM respond
    for keyword, _ in OUT_OF_SCOPE_TOPICS:
        if keyword in lower:
            return True
    return False


def scope_redirect_response() -> str:
    """Standard redirection response for fully off-topic messages."""
    return _SCOPE_REDIRECT


def check_response(response: str, intent: str) -> str:
    """
    Apply safety guardrails to a bot response before delivery.

    Checks (in order):
    1. Forbidden regex patterns (exact prices, fake guarantees, etc.)
    2. Price invention keywords
    3. Out-of-scope topic detection in the LLM's output

    Returns the original response if clean, or a safe replacement.
    """
    lower = response.lower()

    # 1. Forbidden pattern check
    for pattern, label in FORBIDDEN_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            logger.warning(f"Guardrail blocked [{label}]: matched pattern in response")
            return _price_fallback() if "price" in label or label == "exact_price" else _generic_fallback()

    # 2. Price invention keywords
    for keyword in PRICE_INVENTION_KEYWORDS:
        if keyword in lower:
            logger.warning(f"Guardrail blocked [price_keyword]: '{keyword}'")
            return _price_fallback()

    # 3. Out-of-scope content in LLM output
    for keyword, label in OUT_OF_SCOPE_TOPICS:
        if keyword in lower:
            logger.warning(f"Guardrail blocked [out_of_scope/{label}]: '{keyword}'")
            return _SCOPE_REDIRECT

    return response


def _price_fallback() -> str:
    return (
        "El valor depende del alcance: canal de atención, integraciones, "
        "volumen de conversaciones y nivel de personalización. "
        "¿Quieres que el equipo de Crovenett te prepare una propuesta a medida?"
    )


def _generic_fallback() -> str:
    return (
        "No tengo ese dato exacto en este momento. "
        "Puedo derivarte con el equipo de Crovenett para que te orienten en detalle. "
        "¿Te parece bien?"
    )
