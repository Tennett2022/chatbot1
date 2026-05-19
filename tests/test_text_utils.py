"""
Tests for app/utils/text.py
Run with: pytest tests/test_text_utils.py -v
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.text import (
    clean_text,
    truncate,
    chunk_text,
    extract_email,
    extract_phone,
)


class TestCleanText(unittest.TestCase):
    def test_strips_whitespace(self):
        self.assertEqual(clean_text("  hola  "), "hola")

    def test_collapses_internal_spaces(self):
        self.assertEqual(clean_text("hola   mundo"), "hola mundo")

    def test_collapses_newlines(self):
        self.assertEqual(clean_text("hola\nmundo"), "hola mundo")

    def test_empty_string(self):
        self.assertEqual(clean_text(""), "")


class TestTruncate(unittest.TestCase):
    def test_short_text_unchanged(self):
        text = "Hola mundo"
        self.assertEqual(truncate(text, 100), text)

    def test_truncates_long_text(self):
        text = "a" * 5000
        result = truncate(text, 4000)
        self.assertLessEqual(len(result), 4003)  # +3 for "..."
        self.assertTrue(result.endswith("..."))

    def test_exact_length_unchanged(self):
        text = "a" * 4000
        self.assertEqual(truncate(text, 4000), text)


class TestChunkText(unittest.TestCase):
    def test_short_text_returns_single_chunk(self):
        text = "Hola, esto es un mensaje corto."
        chunks = chunk_text(text, max_len=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_long_text_splits_into_multiple_chunks(self):
        text = "Palabra " * 1000  # ~8000 chars
        chunks = chunk_text(text, max_len=4096)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 4096)

    def test_no_empty_chunks(self):
        text = "Hola\n\nMundo\n\nAdiós " * 200
        chunks = chunk_text(text, max_len=100)
        for chunk in chunks:
            self.assertGreater(len(chunk), 0)

    def test_all_content_preserved(self):
        text = "Palabra " * 500
        chunks = chunk_text(text, max_len=200)
        # All words should be present across chunks
        combined = " ".join(chunks)
        # Check approximate content (join may add spaces)
        self.assertGreater(len(combined), len(text) * 0.9)

    def test_empty_text(self):
        chunks = chunk_text("", max_len=100)
        self.assertEqual(chunks, [])

    def test_exactly_max_len(self):
        text = "a" * 4096
        chunks = chunk_text(text, max_len=4096)
        self.assertEqual(len(chunks), 1)


class TestExtractEmail(unittest.TestCase):
    def test_simple_email(self):
        self.assertEqual(extract_email("mi correo es juan@empresa.cl"), "juan@empresa.cl")

    def test_email_at_start(self):
        self.assertEqual(extract_email("contacto@crovenett.cl para más info"), "contacto@crovenett.cl")

    def test_no_email(self):
        self.assertIsNone(extract_email("no hay email aquí"))

    def test_email_with_subdomain(self):
        result = extract_email("escríbeme a usuario@mail.empresa.com")
        self.assertIsNotNone(result)
        self.assertIn("@", result)

    def test_gmail(self):
        self.assertEqual(extract_email("juan.perez@gmail.com"), "juan.perez@gmail.com")

    def test_email_lowercased(self):
        result = extract_email("EMAIL: JUAN@EMPRESA.CL")
        self.assertIsNotNone(result)
        self.assertEqual(result, result.lower())

    def test_email_with_plus(self):
        result = extract_email("ventas+info@empresa.cl")
        self.assertIsNotNone(result)


class TestExtractPhone(unittest.TestCase):
    def test_chilean_mobile(self):
        result = extract_phone("mi teléfono es 912345678")
        self.assertIsNotNone(result)
        self.assertIn("912345678", result)

    def test_chilean_with_country_code(self):
        result = extract_phone("llámame al +56912345678")
        self.assertIsNotNone(result)

    def test_chilean_with_spaces(self):
        result = extract_phone("+56 9 1234 5678")
        self.assertIsNotNone(result)

    def test_no_phone(self):
        result = extract_phone("no hay número aquí")
        self.assertIsNone(result)

    def test_no_false_positive_year(self):
        """A 4-digit year should not be extracted as a phone."""
        result = extract_phone("fundamos la empresa en 2019")
        self.assertIsNone(result)

    def test_no_false_positive_small_number(self):
        """Small numbers like '3 empleados' should not match."""
        result = extract_phone("tengo 3 empleados en mi empresa")
        self.assertIsNone(result)

    def test_no_false_positive_invoice_number(self):
        """An invoice number like 12345678 without phone context should not match."""
        result = extract_phone("la factura número 12345678 está pendiente")
        # The regex requires phone-context words for generic 8-digit numbers
        # This depends on the implementation — document the expected behavior
        # If the regex is strict (requires context), this should be None
        # If it matches any 9-digit starting with 9, only numbers starting with 9 would match
        # "12345678" doesn't start with 9, so it should be None
        self.assertIsNone(result)

    def test_context_phone_word(self):
        """8-digit number with context word 'teléfono' should match."""
        result = extract_phone("teléfono: 22334455")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
