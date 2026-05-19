"""
Tests for app/core/escalation.py
Run with: pytest tests/test_escalation.py -v
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

mock_settings = MagicMock()
mock_settings.LOG_LEVEL = "WARNING"
mock_settings.APP_ENV = "test"

with patch.dict("sys.modules", {"app.config": MagicMock(settings=mock_settings)}):
    from app.core.escalation import should_escalate, get_escalation_response


class TestShouldEscalate(unittest.TestCase):

    def test_hard_intent_soporte_humano(self):
        self.assertTrue(should_escalate("soporte_humano", "quiero hablar con alguien", {}, 0))

    def test_hard_intent_agendar_reunion(self):
        self.assertTrue(should_escalate("agendar_reunion", "quiero agendar una demo", {}, 0))

    def test_soft_intent_cliente_interesado_without_contact(self):
        """cliente_interesado alone (no contact data) should NOT escalate."""
        self.assertFalse(should_escalate("cliente_interesado", "me interesa", {}, 0))

    def test_soft_intent_cliente_interesado_with_contact(self):
        """cliente_interesado + email SHOULD escalate."""
        lead = {"email": "test@test.cl"}
        self.assertTrue(should_escalate("cliente_interesado", "me interesa", lead, 0))

    def test_phrase_trigger_hablar_con_persona(self):
        self.assertTrue(
            should_escalate("informacion_empresa", "quiero hablar con una persona", {}, 0)
        )

    def test_phrase_trigger_contacten(self):
        self.assertTrue(
            should_escalate("precios", "quiero que me contacten", {}, 0)
        )

    def test_phrase_trigger_quiero_contratar(self):
        self.assertTrue(
            should_escalate("precios", "quiero contratar este servicio", {}, 0)
        )

    def test_no_escalation_on_generic_servicios(self):
        """Informational intent with no triggers should NOT escalate."""
        self.assertFalse(should_escalate("servicios", "qué servicios ofrecen", {}, 2))

    def test_no_escalation_on_precio_without_phrases(self):
        """Simple price question should NOT escalate (LLM handles it)."""
        self.assertFalse(should_escalate("precios", "cuánto cuesta un chatbot", {}, 1))

    def test_auto_escalation_complete_lead_many_turns(self):
        """Complete lead after many turns SHOULD auto-escalate."""
        lead = {
            "nombre": "Juan",
            "empresa": "Empresa X",
            "email": "juan@empresa.cl",
        }
        self.assertTrue(should_escalate("precios", "cuánto cuesta?", lead, 6))

    def test_auto_escalation_complete_lead_few_turns(self):
        """Complete lead but only 2 turns should NOT auto-escalate."""
        lead = {
            "nombre": "Juan",
            "empresa": "Empresa X",
            "email": "juan@empresa.cl",
        }
        self.assertFalse(should_escalate("precios", "cuánto cuesta?", lead, 2))

    def test_no_escalation_on_empty_lead(self):
        """No data, no trigger phrase, informational intent — no escalation."""
        self.assertFalse(should_escalate("informacion_empresa", "qué hacen", {}, 0))

    def test_phrase_trigger_precio_exacto(self):
        self.assertTrue(
            should_escalate("precios", "necesito un precio exacto ya", {}, 0)
        )

    def test_phrase_trigger_queja(self):
        self.assertTrue(
            should_escalate("fuera_de_alcance", "tengo una queja formal", {}, 0)
        )

    def test_phrase_trigger_reclamo(self):
        self.assertTrue(
            should_escalate("fuera_de_alcance", "quiero hacer un reclamo", {}, 0)
        )

    def test_no_false_positive_problema(self):
        """'problema' alone should NOT trigger escalation (too broad)."""
        # 'problema' is NOT in ESCALATION_PHRASES — 'tengo un problema' might be context
        # depends on implementation — confirm the exact behavior
        result = should_escalate("automatizacion", "tenemos un problema con nuestros procesos", {}, 0)
        # This should be False unless explicitly added to phrases
        # Verifies we removed the too-broad "problema" trigger
        self.assertFalse(result)


class TestGetEscalationResponse(unittest.TestCase):

    def test_no_data_asks_for_all(self):
        response = get_escalation_response({})
        self.assertIn("nombre", response.lower())
        self.assertIn("empresa", response.lower())
        self.assertIn("correo", response.lower())

    def test_has_name_asks_for_rest(self):
        response = get_escalation_response({"nombre": "Ana"})
        self.assertIn("empresa", response.lower())
        self.assertIn("correo", response.lower())
        # Name should not be requested again
        self.assertNotIn("nombre", response.lower())

    def test_has_all_data_confirms_handoff(self):
        lead = {
            "nombre": "Carlos",
            "empresa": "Empresa X",
            "email": "carlos@empresa.cl",
        }
        response = get_escalation_response(lead)
        # Should NOT ask for more data
        self.assertNotIn("necesito que me indiques", response.lower())
        # Should confirm handoff
        self.assertIn("Carlos", response)
        self.assertIn("carlos@empresa.cl", response)

    def test_has_phone_instead_of_email(self):
        lead = {
            "nombre": "María",
            "empresa": "Mi Empresa",
            "telefono": "912345678",
        }
        response = get_escalation_response(lead)
        self.assertIn("912345678", response)

    def test_response_is_not_empty(self):
        response = get_escalation_response({})
        self.assertGreater(len(response), 20)

    def test_response_professional_tone(self):
        response = get_escalation_response({})
        # Should be professional (no aggression, no slang)
        self.assertNotIn("oye", response.lower())
        self.assertIn("crovenett", response.lower())


if __name__ == "__main__":
    unittest.main()
