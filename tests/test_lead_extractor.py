"""
Tests for the lead extractor module.
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
    from app.core.lead_extractor import extract_lead_data, get_missing_lead_fields
    from app.utils.text import extract_email, extract_phone


class TestExtractEmail(unittest.TestCase):

    def test_simple_email(self):
        result = extract_email("mi correo es juan@empresa.cl")
        self.assertEqual(result, "juan@empresa.cl")

    def test_no_email(self):
        result = extract_email("no tengo email aquí")
        self.assertIsNone(result)

    def test_email_in_middle(self):
        result = extract_email("escríbeme a contacto@crovenett.cl por favor")
        self.assertEqual(result, "contacto@crovenett.cl")

    def test_gmail(self):
        result = extract_email("juan.perez@gmail.com")
        self.assertEqual(result, "juan.perez@gmail.com")


class TestExtractPhone(unittest.TestCase):

    def test_chilean_mobile(self):
        result = extract_phone("mi teléfono es 912345678")
        self.assertIsNotNone(result)
        self.assertIn("912345678", result)

    def test_with_country_code(self):
        result = extract_phone("llámame al +56 9 1234 5678")
        self.assertIsNotNone(result)

    def test_no_phone(self):
        result = extract_phone("no hay número aquí")
        self.assertIsNone(result)


class TestExtractLeadData(unittest.TestCase):

    def test_extract_email(self):
        result = extract_lead_data("mi correo es ana@empresa.cl")
        self.assertIn("email", result)
        self.assertEqual(result["email"], "ana@empresa.cl")

    def test_extract_name_me_llamo(self):
        result = extract_lead_data("me llamo Carlos González")
        self.assertIn("nombre", result)
        self.assertIn("Carlos", result["nombre"])

    def test_extract_name_soy(self):
        result = extract_lead_data("soy María Rodríguez")
        self.assertIn("nombre", result)
        self.assertIn("María", result["nombre"])

    def test_extract_name_mi_nombre_es(self):
        result = extract_lead_data("mi nombre es Pedro Soto")
        self.assertIn("nombre", result)
        self.assertIn("Pedro", result["nombre"])

    def test_extract_company_trabajo_en(self):
        result = extract_lead_data("trabajo en Empresa ABC")
        self.assertIn("empresa", result)
        self.assertIn("Empresa ABC", result["empresa"])

    def test_extract_urgency_high(self):
        result = extract_lead_data("necesito esto urgente cuanto antes")
        self.assertIn("urgencia", result)
        self.assertEqual(result["urgencia"], "alta")

    def test_extract_urgency_low(self):
        result = extract_lead_data("no hay prisa con esto")
        self.assertIn("urgencia", result)
        self.assertEqual(result["urgencia"], "baja")

    def test_extract_rubro_clinica(self):
        result = extract_lead_data("tengo una clínica dental en Santiago")
        self.assertIn("rubro", result)
        self.assertIn("clínica", result["rubro"])

    def test_extract_rubro_restaurante(self):
        result = extract_lead_data("tengo un restaurante de comida italiana")
        self.assertIn("rubro", result)
        self.assertIn("restaurante", result["rubro"])

    def test_extract_rubro_tecnologia(self):
        result = extract_lead_data("somos una startup de tecnología")
        self.assertIn("rubro", result)
        self.assertIn("tecnología", result["rubro"])

    def test_extract_service_whatsapp(self):
        result = extract_lead_data("quiero un chatbot para whatsapp")
        self.assertIn("servicio_interesado", result)
        self.assertEqual(result["servicio_interesado"], "chatbot_whatsapp")

    def test_extract_budget_dollar(self):
        result = extract_lead_data("tengo un presupuesto de $500")
        self.assertIn("presupuesto_estimado", result)

    def test_multiple_fields(self):
        text = "me llamo Juan Silva, trabajo en TechCorp y mi email es juan@techcorp.cl"
        result = extract_lead_data(text)
        self.assertIn("nombre", result)
        self.assertIn("empresa", result)
        self.assertIn("email", result)
        self.assertEqual(result["email"], "juan@techcorp.cl")

    def test_empty_text(self):
        result = extract_lead_data("")
        self.assertEqual(result, {})

    def test_no_lead_data(self):
        result = extract_lead_data("¿cuánto cuesta el servicio?")
        self.assertEqual(result, {})


class TestGetMissingLeadFields(unittest.TestCase):

    def test_all_missing(self):
        missing = get_missing_lead_fields({})
        self.assertIn("nombre", missing)
        self.assertIn("empresa", missing)
        self.assertIn("email", missing)
        self.assertIn("telefono", missing)

    def test_email_present(self):
        missing = get_missing_lead_fields({"email": "test@test.com"})
        self.assertNotIn("email", missing)
        self.assertIn("nombre", missing)

    def test_all_present(self):
        missing = get_missing_lead_fields({
            "nombre": "Juan",
            "empresa": "Empresa",
            "email": "juan@empresa.cl",
            "telefono": "912345678",
        })
        self.assertEqual(missing, [])

    def test_partial_data(self):
        missing = get_missing_lead_fields({
            "nombre": "Ana",
            "empresa": "Mi Empresa",
        })
        self.assertIn("email", missing)
        self.assertIn("telefono", missing)
        self.assertNotIn("nombre", missing)


if __name__ == "__main__":
    unittest.main()
