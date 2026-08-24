"""Tests for legal models, verification rules and versioning behaviour."""

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.languages.models import Language
from apps.legal.models import (
    DISCLAIMER,
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)
from apps.legal.services.content_query import (
    available_languages_for_topic,
    get_verified_content,
)


def make_source(status="ACTIVE", **overrides):
    defaults = dict(
        name="Employment Act, 2006",
        organization="Parliament of Uganda",
        source_type="ACT",
        status=status,
        authority_level=1,
        is_authoritative=True,
        url="https://ulii.org",
    )
    defaults.update(overrides)
    return LegalSource.objects.create(**defaults)


def make_content(topic, language, source, status="DRAFT", **overrides):
    defaults = dict(
        topic=topic,
        language=language,
        source=source,
        title="Unpaid salary",
        summary="Summary text.",
        rights_information="You have rights.",
        what_this_means="In simple terms.",
        next_steps="Seek help.",
        documents_required="Contract, payslips.",
        source_title=source.document_title or source.name,
        source_url=source.url,
        legal_reference="Article 40(1)",
        section_reference="Art. 40(1)",
        last_verified=date.today(),
        verification_status=status,
        disclaimer=DISCLAIMER,
    )
    defaults.update(overrides)
    return LegalContent.objects.create(**defaults)


class LegalContentVerificationTests(TestCase):
    def setUp(self):
        self.source = make_source()
        self.category = LegalCategory.objects.create(
            name="Employment", slug="employment"
        )
        self.topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=self.category
        )
        self.en = Language.objects.create(code="en", name="English", is_default=True)
        self.lg = Language.objects.create(code="lg", name="Luganda")

    def test_source_required_for_verified(self):
        content = LegalContent(
            topic=self.topic,
            language=self.en,
            title="No source",
            legal_reference="X",
            last_verified=date.today(),
            verification_status="VERIFIED",
            source=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            content.full_clean()
        self.assertIn("source", ctx.exception.message_dict)

    def test_legal_reference_required_for_verified(self):
        content = LegalContent(
            topic=self.topic,
            language=self.en,
            source=self.source,
            title="No ref",
            last_verified=date.today(),
            verification_status="VERIFIED",
        )
        with self.assertRaises(ValidationError) as ctx:
            content.full_clean()
        self.assertIn("legal_reference", ctx.exception.message_dict)

    def test_last_verified_required_for_verified(self):
        content = LegalContent(
            topic=self.topic,
            language=self.en,
            source=self.source,
            title="No date",
            legal_reference="Art 40(1)",
            last_verified=None,
            verification_status="VERIFIED",
        )
        with self.assertRaises(ValidationError) as ctx:
            content.full_clean()
        self.assertIn("last_verified", ctx.exception.message_dict)

    def test_draft_does_not_require_source(self):
        content = LegalContent.objects.create(
            topic=self.topic,
            language=self.en,
            title="Draft only",
            verification_status="DRAFT",
        )
        self.assertEqual(content.verification_status, "DRAFT")

    def test_verified_content_visible_only_verified(self):
        make_content(self.topic, self.en, self.source, status="VERIFIED")
        make_content(self.topic, self.lg, self.source, status="DRAFT", title="Draft lg")
        self.assertIsNotNone(get_verified_content(self.topic, "en"))
        self.assertIsNone(get_verified_content(self.topic, "lg"))
        # English fallback only for non-verified request languages
        self.assertIsNone(get_verified_content(self.topic, "ach"))

    def test_available_languages(self):
        make_content(self.topic, self.en, self.source, status="VERIFIED")
        make_content(self.topic, self.lg, self.source, status="DRAFT")
        codes = available_languages_for_topic(self.topic)
        self.assertEqual(codes, ["en"])

    def test_repealed_source_status_message(self):
        source = make_source(status="REPEALED")
        self.assertEqual(source.status_display_message(), "This law has been repealed.")
        source.status = "AMENDED"
        self.assertEqual(
            source.status_display_message(),
            "This law has been amended. View the current version.",
        )
        source.status = "UNCOMMENCED"
        self.assertEqual(
            source.status_display_message(), "This provision has not yet commenced."
        )
        source.status = "ACTIVE"
        self.assertEqual(source.status_display_message(), "")

    def test_source_requires_review_flag(self):
        source = make_source(status="ACTIVE")  # no last_verified_at
        self.assertTrue(source.requires_review)
        from apps.legal.services.source_service import SourceService

        SourceService.mark_verified(source)
        source.refresh_from_db()
        self.assertFalse(source.requires_review)

    def test_save_populates_source_title_and_url(self):
        src = make_source(
            name="Constitution of Uganda",
            document_title="Constitution 1995",
            url="https://example.com",
        )
        content = LegalContent.objects.create(
            topic=self.topic,
            language=self.en,
            source=src,
            title="T",
            verification_status="DRAFT",
        )
        self.assertEqual(content.source_title, "Constitution 1995")
        self.assertEqual(content.source_url, "https://example.com")

    def test_get_verified_content_requires_verbatim_topic(self):
        make_content(self.topic, self.en, self.source, status="VERIFIED")
        other = LegalTopic.objects.create(
            name="Dismissal", slug="dismissal", category=self.category
        )
        self.assertIsNone(get_verified_content(other, "en"))

    def test_status_message_versioning_display(self):
        # API level: amended/repealed status surfaced through source.status_message
        source = make_source(status="REPEALED")
        make_content(self.topic, self.en, source, status="VERIFIED")
        response = self.client.get(f"/api/legal/topics/{self.topic.slug}/?lang=en")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data["content"]["source"]["status_message"], "This law has been repealed."
        )

    def test_draft_content_hidden_from_public_api(self):
        make_content(self.topic, self.en, self.source, status="DRAFT")
        self.assertEqual(self.client.get("/api/legal/topics/").json(), [])
        response = self.client.get(f"/api/legal/topics/{self.topic.slug}/?lang=en")
        self.assertEqual(response.json()["content"], None)
        self.assertEqual(response.json()["available_languages"], [])
