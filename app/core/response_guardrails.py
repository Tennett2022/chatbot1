import re
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Patterns the bot should never produce
FORBIDDEN_PATTERNS = [
    r'\$\s*\d+(?:\.\d+)?(?:\s*(?:mensuales?|anuales?|mensual|anual))?\s*(?:fijos?|exactos?)',
    r'garantiz(?:amos?|o)\s+(?:que|el\s+resultado)',
    r'somos?\s+(?:los?\s+)?(?:mejores?|n[uú]mero\s+uno)',
    r'nuestros?\s+clientes?\s+(?:incluyen?|son?)\s+(?:Amazon|Google|Apple)',
    r'certificado\s+(?:por|de)\s+(?:ISO|Google|Microsoft)',
]

PRICE_INVENTION_KEYWORDS = [
    "cuesta exactamente",
    "el precio es",
    "vale exactamente",
    "cobraremos exactamente",
    "precio fijo de",
]

OUT_OF_SCOPE_TOPICS = [
    "política",
    "religión",
    "inversiones",
    "acciones",
    "bolsa",
    "receta médica",
    "diagnóstico",
    "asesoría legal",
    "asesoría jurídica",
]


def check_response(response: str, intent: str) -> str:
    """
    Apply guardrails to the bot response.
    Returns the (possibly modified) response.
    """
    # Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            logger.warning("Guardrail triggered: forbidden pattern matched")
            return _safe_fallback(intent)

    # Check for price invention
    for keyword in PRICE_INVENTION_KEYWORDS:
        if keyword in response.lower():
            logger.warning(f"Guardrail triggered: price invention keyword '{keyword}'")
            return (
                "El valor depende del alcance de tu proyecto: canal de atención, "
                "integraciones requeridas, volumen de conversaciones y nivel de personalización. "
                "¿Quieres que el equipo de Crovenett te prepare una propuesta a medida?"
            )

    # Check for out-of-scope topics
    for topic in OUT_OF_SCOPE_TOPICS:
        if topic in response.lower():
            logger.warning(f"Guardrail triggered: out-of-scope topic '{topic}'")
            return (
                "Eso está un poco fuera de mi área de conocimiento. "
                "Me especializo en soluciones de IA, automatización y chatbots para empresas. "
                "¿Hay algo en esa área en que te pueda ayudar?"
            )

    return response


def _safe_fallback(intent: str) -> str:
    return (
        "No tengo ese dato exacto en este momento, pero puedo derivarte con el equipo de "
        "Crovenett para que te orienten en detalle. ¿Te parece bien?"
    )
