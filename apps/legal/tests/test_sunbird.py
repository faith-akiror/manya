"""Tests for the Sunbird AI translation service (mocked API)."""

from unittest.mock import Mock

import pytest
from django.test import TestCase

from apps.languages.models import Language
from apps.languages.services.sunbird import (
    SunbirdConfigurationError,
    SunbirdTranslationError,
    SunbirdTranslationService,
)
from apps.legal.models import (
    DISCLAIMER,
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)


def fake_response(status_code=200, payload=None):
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = payload or {}
    return resp


class SunbirdServiceTests(TestCase):
    def setUp(self):
        self.service = SunbirdTranslationService(
            token="fake-token", base_url="https://api.sunbird.ai", timeout=5
        )

    def test_not_configured(self):
        svc = SunbirdTranslationService(token="", base_url="https://api.sunbird.ai")
        self.assertFalse(svc.is_configured())

    def test_translate_success(self):
        self.service.http.post = Mock(
            return_value=fake_response(200, {"translation": "Omuliro"})
        )
        result = self.service.translate("Fire", "lug")
        self.assertEqual(result, "Omuliro")
        args = self.service.http.post.call_args
        self.assertIn("/tasks/translate", args[0][0])
        self.assertEqual(args[1]["json"]["target_language"], "lug")
        self.assertEqual(args[1]["json"]["text"], "Fire")

    def test_translate_missing_token_raises(self):
        svc = SunbirdTranslationService(token="", base_url="https://x")
        with pytest.raises(SunbirdConfigurationError):
            svc.translate("Fire", "lug")

    def test_translate_api_failure(self):
        self.service.http.post = Mock(return_value=fake_response(500, {}))
        with pytest.raises(SunbirdTranslationError):
            self.service.translate("Fire", "lug")

    def test_translate_timeout(self):
        import requests

        def boom(*a, **k):
            raise requests.exceptions.Timeout()

        self.service.http.post = Mock(side_effect=boom)
        with pytest.raises(SunbirdTranslationError):
            self.service.translate("Fire", "lug")

    def test_translate_invalid_response(self):
        self.service.http.post = Mock(return_value=fake_response(200, "not a dict"))
        with pytest.raises(SunbirdTranslationError):
            self.service.translate("Fire", "lug")

    def test_translate_empty_response(self):
        self.service.http.post = Mock(return_value=fake_response(200, {}))
        with pytest.raises(SunbirdTranslationError):
            self.service.translate("Fire", "lug")

    def test_get_supported_languages_fallback(self):
        self.service.http.get = Mock(side_effect=Exception("down"))
        codes = self.service.get_supported_languages()
        self.assertIn("lug", codes)
        self.assertIn("ach", codes)

    def test_translate_content_creates_draft_only(self):
        en = Language.objects.create(code="en", name="English", is_default=True)
        lg = Language.objects.create(code="lg", name="Luganda")
        src = LegalSource.objects.create(
            name="Constitution", source_type="CONSTITUTION", url="https://x"
        )
        cat = LegalCategory.objects.create(name="Employment", slug="employment")
        topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=cat
        )
        content = LegalContent.objects.create(
            topic=topic,
            language=en,
            source=src,
            title="Unpaid salary",
            summary="You are entitled to pay.",
            legal_reference="Art 40(1)",
            verification_status="VERIFIED",
            last_verified="2025-01-01",
            disclaimer=DISCLAIMER,
        )

        from apps.legal.services.translation_service import TranslationWorkflow

        translated_fields = {
            "title": "Omusaala ogutabaddenga",
            "summary": "Olina eddembe okufuna omusaala.",
        }

        class FakeSunbird:
            def translate_content(self, content, target_language):
                return translated_fields

        workflow = TranslationWorkflow(sunbird=FakeSunbird())
        draft = workflow.generate_translation(content, lg)
        self.assertEqual(draft.verification_status, "DRAFT")  # never auto-verified
        self.assertEqual(draft.language, lg)
        self.assertEqual(draft.summary, translated_fields["summary"])
        self.assertIsNone(draft.last_verified)
        self.assertEqual(draft.original_content, content)

    def test_translate_content_preserves_untranslated_fields(self):
        en = Language.objects.create(code="en", name="English", is_default=True)
        lg = Language.objects.create(code="lg", name="Luganda")
        src = LegalSource.objects.create(
            name="Constitution", source_type="CONSTITUTION"
        )
        cat = LegalCategory.objects.create(name="Employment", slug="employment")
        topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=cat
        )
        content = LegalContent.objects.create(
            topic=topic,
            language=en,
            source=src,
            title="T",
            summary="S",
            what_this_means="W",
            verification_status="DRAFT",
        )

        from apps.legal.services.translation_service import TranslationWorkflow

        class FakeSunbird:
            def translate_content(self, content, target_language):
                return {"title": "Translated title"}

        workflow = TranslationWorkflow(sunbird=FakeSunbird())
        draft = workflow.generate_translation(content, lg)
        self.assertEqual(draft.title, "Translated title")
        # Untranslated fields keep source-language values (never lost)
        self.assertEqual(draft.summary, "S")
        self.assertEqual(draft.what_this_means, "W")

    def test_generate_translation_blocks_same_language(self):
        en = Language.objects.create(code="en", name="English", is_default=True)
        src = LegalSource.objects.create(
            name="Constitution", source_type="CONSTITUTION"
        )
        cat = LegalCategory.objects.create(name="Employment", slug="employment")
        topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=cat
        )
        content = LegalContent.objects.create(
            topic=topic,
            language=en,
            source=src,
            title="T",
            verification_status="DRAFT",
        )
        from apps.legal.services.translation_service import TranslationWorkflow

        workflow = TranslationWorkflow(sunbird=Mock())
        with pytest.raises(ValueError):
            workflow.generate_translation(content, en)
