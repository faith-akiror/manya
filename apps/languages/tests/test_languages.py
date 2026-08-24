"""Tests for the dynamic language system."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.languages.models import Language, UIMessage
from apps.languages.services.ui_translations import UITranslationService


class LanguageModelTests(TestCase):
    def test_create_language(self):
        lang = Language.objects.create(
            code="nyn", name="Runyankole", native_name="Runyankore", display_order=9
        )
        self.assertEqual(Language.objects.count(), 1)
        self.assertEqual(str(lang), "Runyankole")

    def test_duplicate_code_rejected(self):
        Language.objects.create(code="en", name="English")
        with self.assertRaises(IntegrityError):
            Language.objects.create(code="en", name="English Again")

    def test_single_default(self):
        a = Language.objects.create(code="aa", name="A", is_default=True)
        b = Language.objects.create(code="bb", name="B", is_default=True)
        self.assertTrue(Language.objects.filter(is_default=True).count() <= 1)
        a.refresh_from_db()
        self.assertFalse(a.is_default)
        b.refresh_from_db()
        self.assertTrue(b.is_default)

    def test_active_public(self):
        lang = Language.objects.create(code="lg", name="Luganda", is_active=True)
        self.assertIn(lang, list(Language.active_public()))
        lang.is_active = False
        lang.save()
        self.assertNotIn(lang, list(Language.active_public()))

    def test_lookup_default(self):
        Language.objects.create(code="en", name="English", is_default=True)
        self.assertEqual(Language.get_default().code, "en")

    def test_clean_rejects_second_default(self):
        Language.objects.create(code="en", name="English", is_default=True)
        lg = Language(code="lg", name="Luganda", is_default=True)
        with self.assertRaises(ValidationError):
            lg.full_clean()


class UIMessageTests(TestCase):
    def test_message_unique_per_language(self):
        lang = Language.objects.create(code="lg", name="Luganda")
        UIMessage.objects.create(language=lang, key="home", text="Enju")
        with self.assertRaises(IntegrityError):
            UIMessage.objects.create(language=lang, key="home", text="Dup")

    def test_ui_resolution_falls_back_to_english(self):
        Language.objects.create(code="en", name="English", is_default=True)
        lg = Language.objects.create(code="lg", name="Luganda")
        UIMessage.objects.create(language=lg, key="home", text="Enju")
        self.assertEqual(UITranslationService.get("home", "en"), "Home")
        self.assertEqual(UITranslationService.get("home", "lg"), "Enju")
        self.assertEqual(UITranslationService.get("unknown_key", "lg"), "unknown_key")


class LanguageAPITests(TestCase):
    def test_list_returns_active_public_languages(self):
        Language.objects.create(
            code="en", name="English", is_default=True, display_order=1
        )
        Language.objects.create(code="lg", name="Luganda", display_order=2)
        Language.objects.create(
            code="zz", name="Hidden", is_active=False, display_order=3
        )

        response = self.client.get("/api/languages/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        codes = [item["code"] for item in payload]
        self.assertEqual(codes, ["en", "lg"])

    def test_language_api_is_driven_by_db(self):
        Language.objects.create(code="nyn", name="Runyankole", display_order=1)
        response = self.client.get("/api/languages/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["code"], "nyn")

    def test_inactive_language_hidden(self):
        Language.objects.create(code="en", name="English", is_active=True)
        Language.objects.create(code="lg", name="Luganda", is_active=False)
        response = self.client.get("/api/languages/")
        self.assertEqual(len(response.json()), 1)
