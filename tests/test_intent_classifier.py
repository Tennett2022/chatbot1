"""
Tests for the intent classifier module.
"""
import sys
import os

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock settings before importing modules that depend on it
import unittest
from unittest.mock import patch, MagicMock

# Create a minimal settings mock
mock_settings = MagicMock()
mock_settings.LOG_LEVEL = "INFO"
mock_settings.LLM_PROVIDER = "openai"
mock_settings.OPENAI_MODEL = "gpt-4o-mini"
mock_settings.ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"
mock_settings.GEMINI_MODEL = "gemini-1.5-flash"
mock_settings.APP_ENV = "test"
mock_settings.DATABASE_URL = "sqlite:///./test.db"
mock_settings.TELEGRAM_BOT_TOKEN = "test-token"
mock_settings.TELEGRAM_WEBHOOK_SECRET = ""
mock_settings.WHATSAPP_PROVIDER = ""
mock_settings.WHATSAPP_TOKEN = ""
mock_settings.WHATSAPP_PHONE_NUMBER_ID = ""
mock_settings.WHATSAPP_VERIFY_TOKEN = ""
mock_settings.OPENAI_API_KEY = ""
mock_settings.ANTHROPIC_API_KEY = ""
mock_settings.GEMINI_API_KEY = ""
mock_settings.ESCALATION_EMAIL = "test@test.cl"
mock_settings.ESCALATION_PHONE = "+56 9 1234 5678"
mock_settings.MAX_HISTORY_MESSAGES = 10

with patch.dict("sys.modules", {"app.config": MagicMock(settings=mock_settings)}):
    from app.core.intent_classifier import classify_intent, INTENTS


class TestIntentClassifier(unittest.TestCase):

    def test_saludo_hola(self):
        intent, confidence = classify_intent("hola")
        self.assertEqual(intent, "saludo")
        self.assertGreater(confidence, 0.5)

    def test_saludo_buenos_dias(self):
        intent, confidence = classify_intent("buenos días")
        self.assertEqual(intent, "saludo")

    def test_saludo_hey(self):
        intent, confidence = classify_intent("Hey, ¿cómo están?")
        self.assertEqual(intent, "saludo")

    def test_precios(self):
        intent, confidence = classify_intent("¿cuánto cuesta un chatbot?")
        self.assertEqual(intent, "precios")

    def test_precios_tarifa(self):
        intent, confidence = classify_intent("¿cuál es la tarifa mensual?")
        self.assertEqual(intent, "precios")

    def test_precios_cotizacion(self):
        intent, confidence = classify_intent("necesito una cotización")
        self.assertEqual(intent, "precios")

    def test_servicios(self):
        intent, confidence = classify_intent("¿qué servicios ofrecen?")
        self.assertEqual(intent, "servicios")

    def test_chatbot_whatsapp(self):
        intent, confidence = classify_intent("quiero un chatbot para WhatsApp")
        self.assertEqual(intent, "chatbot_whatsapp")

    def test_chatbot_whatsapp_reverse(self):
        intent, confidence = classify_intent("bot de whatsapp para mi empresa")
        self.assertEqual(intent, "chatbot_whatsapp")

    def test_chatbot_web(self):
        intent, confidence = classify_intent("quiero un chatbot en mi página web")
        self.assertEqual(intent, "chatbot_web")

    def test_voicebot(self):
        intent, confidence = classify_intent("necesito un voicebot para llamadas")
        self.assertEqual(intent, "voicebot")

    def test_automatizacion(self):
        intent, confidence = classify_intent("quiero automatizar mis procesos con n8n")
        self.assertEqual(intent, "automatizacion")

    def test_integraciones_crm(self):
        intent, confidence = classify_intent("¿pueden integrar con HubSpot CRM?")
        self.assertEqual(intent, "integraciones")

    def test_agendar_reunion(self):
        intent, confidence = classify_intent("quiero agendar una demo")
        self.assertEqual(intent, "agendar_reunion")

    def test_soporte_humano(self):
        intent, confidence = classify_intent("quiero hablar con una persona")
        self.assertEqual(intent, "soporte_humano")

    def test_cliente_interesado(self):
        intent, confidence = classify_intent("me interesa contratar el servicio")
        self.assertEqual(intent, "cliente_interesado")

    def test_despedida(self):
        intent, confidence = classify_intent("adiós, hasta luego")
        self.assertEqual(intent, "despedida")

    def test_informacion_empresa(self):
        intent, confidence = classify_intent("¿qué hace Crovenett?")
        self.assertEqual(intent, "informacion_empresa")

    def test_leads(self):
        intent, confidence = classify_intent("necesito generar más leads")
        self.assertEqual(intent, "generacion_leads")

    def test_fuera_de_alcance(self):
        intent, confidence = classify_intent("¿cuál es la capital de Francia?")
        self.assertEqual(intent, "fuera_de_alcance")
        self.assertEqual(confidence, 0.3)

    def test_case_insensitive(self):
        intent, confidence = classify_intent("HOLA BUENOS DÍAS")
        self.assertEqual(intent, "saludo")

    def test_empty_string_fallback(self):
        intent, confidence = classify_intent("")
        self.assertEqual(intent, "fuera_de_alcance")

    def test_all_intents_have_patterns(self):
        """All defined intents should have at least one pattern."""
        for intent_name, patterns in INTENTS.items():
            self.assertGreater(len(patterns), 0, f"Intent '{intent_name}' has no patterns")

    def test_confidence_for_match(self):
        _, confidence = classify_intent("hola buenas tardes")
        self.assertEqual(confidence, 0.9)

    def test_confidence_for_no_match(self):
        _, confidence = classify_intent("xyzabc 123 nosentido")
        self.assertEqual(confidence, 0.3)


if __name__ == "__main__":
    unittest.main()
