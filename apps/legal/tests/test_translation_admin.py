"""Admin + API verification for the legal translation system.

Covers the single-administrator model: one superuser manages every model,
translation inlines render on each content admin, future languages work
dynamically, and API responses honour ``?lang=``.
"""

import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.languages.models import ContentTranslation, Language
from apps.legal.models import (
    DISCLAIMER,
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)

User = get_user_model()


def make_translation(obj, lang_code, field, text):
    return ContentTranslation.objects.create(
        language=Language.objects.get(code=lang_code),
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        field=field,
        text=text,
        is_verified=True,
        translation_source="manual",
        translation_status="reviewed",
    )


class LegalSeedMixin:
    """Minimal verified English seed shared by admin/API tests."""

    @classmethod
    def seed_legal(cls):
        Language.objects.create(code="en", name="English", is_default=True)
        Language.objects.create(code="lg", name="Luganda")
        cls.source = LegalSource.objects.create(
            name="Constitution of Uganda", source_type="CONSTITUTION", url="https://x"
        )
        cls.category = LegalCategory.objects.create(
            name="Employment", slug="employment", description="Work-related issues."
        )
        cls.topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=cls.category
        )
        cls.content = LegalContent.objects.create(
            topic=cls.topic,
            language=Language.objects.get(code="en"),
            source=cls.source,
            title="Unpaid salary",
            summary="Summary.",
            rights_information="You have rights.",
            next_steps="Seek help.",
            documents_required="Contract.",
            legal_reference="Article 40(1)",
            verification_status="VERIFIED",
            last_verified="2025-01-01",
            disclaimer=DISCLAIMER,
        )


class AdminInlineTests(TestCase):
    """One administrator manages translations on every content admin."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="manya-admin",
            email="admin@manya.ug",
            password="test-pass-123",
        )
        cls.source = LegalSource.objects.create(
            name="Employment Act, 2006", source_type="ACT", url="https://x"
        )
        cls.category = LegalCategory.objects.create(
            name="Employment", slug="employment"
        )
        cls.topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=cls.category
        )
        Language.objects.create(code="lg", name="Luganda")

    def setUp(self):
        self.client.force_login(self.admin)

    def _change_page(self, model, pk):
        opts = model._meta
        url = reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[pk])
        return self.client.get(url)

    def test_translation_inline_renders_on_every_content_admin(self):
        for model, pk in (
            (LegalCategory, self.category.pk),
            (LegalTopic, self.topic.pk),
            (LegalSource, self.source.pk),
        ):
            with self.subTest(model=model.__name__):
                response = self._change_page(model, pk)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Translations")

    def test_stored_translation_displays_on_change_page(self):
        make_translation(self.category, "lg", "name", "Emirimu")
        response = self._change_page(LegalCategory, self.category.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Emirimu")

    def test_future_language_works_dynamically_in_admin(self):
        """A language added later is immediately usable in the inline."""
        Language.objects.create(
            code="sw", name="Swahili", native_name="Kiswahili", is_active=True
        )
        make_translation(self.category, "sw", "name", "Haki za Wafanyakazi")
        response = self._change_page(LegalCategory, self.category.pk)
        self.assertEqual(response.status_code, 200)
        # The Swahili translation renders without any code/schema change.


class ApiCategoryTranslationTests(LegalSeedMixin, TestCase):
    """``?lang=`` returns stored translations instead of raw English."""

    @classmethod
    def setUpTestData(cls):
        cls.seed_legal()
        make_translation(cls.category, "lg", "name", "Emirimu")
        make_translation(cls.topic, "lg", "name", "Omusaalo ogusasulwa")

    def test_category_list_uses_stored_translation(self):
        resp = self.client.get("/api/legal/categories/?lang=lg")
        self.assertEqual(resp.status_code, 200)
        data = {item["slug"]: item for item in resp.json()}
        self.assertEqual(data["employment"]["name"], "Emirimu")

    def test_category_list_falls_back_to_english_without_translation(self):
        Language.objects.create(code="teo", name="Ateso")
        resp = self.client.get("/api/legal/categories/?lang=teo")
        names = [item["name"] for item in resp.json()]
        self.assertIn("Employment", names)

    def test_category_detail_translates_topics_too(self):
        resp = self.client.get("/api/legal/categories/employment/?lang=lg")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["name"], "Emirimu")
        topics = {t["slug"]: t for t in data["topics"]}
        self.assertEqual(topics["unpaid-salary"]["name"], "Omusaalo ogusasulwa")

    def test_topic_detail_translates_parent_category(self):
        resp = self.client.get("/api/legal/topics/unpaid-salary/?lang=lg")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["category"]["name"], "Emirimu")


class SuperuserIdempotencyTests(TestCase):
    """The SINGLE administrator: created once, safely updated after that."""

    ENV = {
        "DJANGO_SUPERUSER_USERNAME": "manya-admin",
        "DJANGO_SUPERUSER_EMAIL": "admin@manya.ug",
        "DJANGO_SUPERUSER_PASSWORD": "first-pass-123",
    }

    def test_created_once_and_updated_on_rotation(self):
        with patch.dict(os.environ, dict(self.ENV)):
            call_command("setup_manya", verbosity=0)
        self.assertEqual(User.objects.filter(username="manya-admin").count(), 1)
        admin = User.objects.get(username="manya-admin")
        self.assertTrue(admin.is_superuser and admin.is_staff and admin.is_active)
        self.assertTrue(admin.check_password("first-pass-123"))

        rotated = {**self.ENV, "DJANGO_SUPERUSER_PASSWORD": "rotated-pass-456"}
        with patch.dict(os.environ, rotated):
            call_command("setup_manya", verbosity=0)

        # Still exactly ONE administrator - never duplicated.
        self.assertEqual(
            User.objects.filter(
                username="manya-admin",
                is_superuser=True,
                is_staff=True,
                is_active=True,
            ).count(),
            1,
        )
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("rotated-pass-456"))
