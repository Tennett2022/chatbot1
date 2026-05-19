"""
Tests for the prompt builder module.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

mock_settings = MagicMock()
mock_settings.LOG_LEVEL = "INFO"
mock_settings.APP_ENV = "test"

with patch.dict("sys.modules", {"app.config": MagicMock(settings=mock_settings)}):
    from app.core.prompt_builder import build_system_prompt, build_conversation_messages


class TestBuildSystemPrompt(unittest.TestCase):

    def test_prompt_is_string(self):
        prompt = build_system_prompt()
        self.assertIsInstance(prompt, str)

    def test_prompt_not_empty(self):
        prompt = build_system_prompt()
        self.assertGreater(len(prompt), 100)

    def test_prompt_contains_crovenett(self):
        prompt = build_system_prompt()
        self.assertIn("Crovenett", prompt)

    def test_prompt_contains_rules(self):
        prompt = build_system_prompt()
        self.assertIn("REGLAS", prompt)

    def test_prompt_with_lead_data_name(self):
        lead_data = {"nombre": "Juan Pérez", "empresa": "Empresa ABC"}
        prompt = build_system_prompt(lead_data=lead_data)
        self.assertIn("Juan Pérez", prompt)
        self.assertIn("Empresa ABC", prompt)

    def test_prompt_with_partial_lead_data(self):
        lead_data = {"email": "test@test.cl"}
        prompt = build_system_prompt(lead_data=lead_data)
        self.assertIn("test@test.cl", prompt)

    def test_prompt_with_empty_lead_data(self):
        prompt = build_system_prompt(lead_data={})
        self.assertIsInstance(prompt, str)
        self.assertNotIn("DATOS CONOCIDOS", prompt)

    def test_prompt_with_none_lead_data(self):
        prompt = build_system_prompt(lead_data=None)
        self.assertIsInstance(prompt, str)

    def test_prompt_with_null_fields_ignored(self):
        lead_data = {"nombre": None, "empresa": None, "email": "test@test.cl"}
        prompt = build_system_prompt(lead_data=lead_data)
        # Should include email but not None values as meaningful content
        self.assertIn("test@test.cl", prompt)

    def test_prompt_contains_tone_guidelines(self):
        prompt = build_system_prompt()
        self.assertIn("TONO", prompt)

    def test_prompt_contains_knowledge_base_section(self):
        prompt = build_system_prompt()
        self.assertIn("BASE DE CONOCIMIENTO", prompt)


class TestBuildConversationMessages(unittest.TestCase):

    def test_empty_history(self):
        messages = build_conversation_messages([])
        self.assertEqual(messages, [])

    def test_single_exchange(self):
        history = [
            {"message_in": "Hola", "message_out": "¡Hola! ¿En qué te ayudo?"}
        ]
        messages = build_conversation_messages(history)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hola")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "¡Hola! ¿En qué te ayudo?")

    def test_multiple_exchanges(self):
        history = [
            {"message_in": "Hola", "message_out": "¡Hola!"},
            {"message_in": "¿Qué hacen?", "message_out": "Somos una empresa de IA."},
            {"message_in": "¿Cuánto cuesta?", "message_out": "Depende del alcance."},
        ]
        messages = build_conversation_messages(history)
        self.assertEqual(len(messages), 6)

    def test_roles_alternate(self):
        history = [
            {"message_in": "Hola", "message_out": "¡Hola!"},
        ]
        messages = build_conversation_messages(history)
        roles = [m["role"] for m in messages]
        self.assertEqual(roles, ["user", "assistant"])

    def test_message_without_in(self):
        history = [
            {"message_in": "", "message_out": "Respuesta"}
        ]
        messages = build_conversation_messages(history)
        # Empty message_in should not be added
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "assistant")

    def test_message_without_out(self):
        history = [
            {"message_in": "Pregunta", "message_out": ""}
        ]
        messages = build_conversation_messages(history)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")

    def test_content_preserved(self):
        text_in = "¿Tienen integración con HubSpot?"
        text_out = "Sí, podemos integrar con HubSpot."
        history = [{"message_in": text_in, "message_out": text_out}]
        messages = build_conversation_messages(history)
        self.assertEqual(messages[0]["content"], text_in)
        self.assertEqual(messages[1]["content"], text_out)


class TestResponseGuardrails(unittest.TestCase):

    def setUp(self):
        with patch.dict("sys.modules", {"app.config": MagicMock(settings=mock_settings)}):
            from app.core.response_guardrails import check_response
            self.check_response = check_response

    def test_clean_response_unchanged(self):
        response = "Podemos ayudarte con un chatbot para WhatsApp."
        result = self.check_response(response, "chatbot_whatsapp")
        self.assertEqual(result, response)

    def test_price_invention_blocked(self):
        response = "El precio es $500 exactos por mes."
        result = self.check_response(response, "precios")
        self.assertNotIn("$500", result)
        self.assertIn("depende", result.lower())

    def test_guarantee_blocked(self):
        response = "Garantizamos que obtendrás resultados."
        result = self.check_response(response, "servicios")
        self.assertNotIn("Garantizamos", result)

    def test_out_of_scope_blocked(self):
        response = "Sobre política, puedo decirte que..."
        result = self.check_response(response, "fuera_de_alcance")
        self.assertNotIn("política", result.lower())


if __name__ == "__main__":
    unittest.main()
