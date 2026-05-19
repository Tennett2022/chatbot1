import re
from app.utils.logger import get_logger

logger = get_logger(__name__)

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
    # Inventing specific integration names as confirmed ("tenemos integración con X" for unknown systems)
    (r'\btenemos\s+integración\s+nativa\s+con\b', "invented_native_integration"),
]

# ── Keyword-only price invention check ───────────────────────────────────────
# These are matched against the lowercased response.
# NOTE: "el precio es" alone is NOT here — too broad.
# Only trigger on patterns that unambiguously invent a closed price.
PRICE_INVENTION_KEYWORDS: list[str] = [
    "precio fijo de $",
    "tarifa fija de $",
    "cuesta exactamente $",
    "cobraremos exactamente",
    "vale exactamente $",
    "inversión de $",          # "la inversión es de $XX"
]

# ── Topics completely out of Crovenett's scope ────────────────────────────────
# Tuple of (keyword_to_detect, label_for_log, replacement_topic_label)
OUT_OF_SCOPE_TOPICS: list[tuple[str, str]] = [
    ("asesoría legal", "legal_advice"),
    ("asesoría jurídica", "legal_advice"),
    ("diagnóstico médico", "medical"),
    ("receta médica", "medical"),
    ("tratamiento médico", "medical"),
    ("inversiones en bolsa", "finance"),
    ("comprar acciones", "finance"),
    ("criptomonedas como inversión", "finance"),
    ("partido político", "politics"),
    ("candidato político", "politics"),
]


def check_response(response: str, intent: str) -> str:
    """
    Apply safety guardrails to a bot response before delivery.

    Checks (in order):
    1. Forbidden regex patterns (exact prices, fake guarantees, etc.)
    2. Price invention keywords
    3. Out-of-scope topic detection

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

    # 3. Out-of-scope topics
    for keyword, label in OUT_OF_SCOPE_TOPICS:
        if keyword in lower:
            logger.warning(f"Guardrail blocked [out_of_scope/{label}]: '{keyword}'")
            return (
                "Ese tema está fuera de mi área. Me especializo en soluciones de IA, "
                "automatización y chatbots para empresas. ¿Te puedo orientar en algo de eso?"
            )

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
