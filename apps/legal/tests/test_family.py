"""Family legal-information journey: database, translation, USSD, SMS, API."""

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.languages.models import ContentTranslation, Language
from apps.languages.services.sunbird_translation import SunbirdTranslationService
from apps.languages.services.translation_service import (
    TRANSLATABLE_MODELS,
    TranslationService,
)
from apps.legal.data.family_i18n import FAMILY_TOPIC_I18N, translation_fields_for_topic
from apps.legal.data.family_seed import FAMILY_SOURCES, FAMILY_TOPICS
from apps.legal.models import LegalCategory, LegalContent, LegalSource, LegalTopic
from apps.ussd.services.ussd_service import UssdService

SUNBIRD_ON = override_settings(SUNBIRD_ENABLED=True, SUNBIRD_API_TOKEN="fake-token")
CONTENT_FIELDS = TRANSLATABLE_MODELS["LegalContent"]["fields"]
REQUIRED_FAMILY_SLUGS = {
    "family-child-maintenance",
    "family-child-custody",
    "family-domestic-violence",
    "family-inheritance",
    "family-wills",
    "family-probate",
    "family-guardianship",
    "family-adoption",
    "family-protection-orders",
    "family-paternity",
    "family-birth-registration",
}


def _translation(obj, lang_code, field):
    return ContentTranslation.objects.filter(
        language__code=lang_code,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        field=field,
    ).first()


class FamilySeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_manya")

    def test_family_category_exists_once(self):
        self.assertEqual(LegalCategory.objects.filter(slug="family").count(), 1)
        family = LegalCategory.objects.get(slug="family")
        self.assertTrue(family.is_active)
        self.assertEqual(family.display_order, 3)

    def test_family_topics_and_content_exist_without_duplicates(self):
        family = LegalCategory.objects.get(slug="family")
        topics = LegalTopic.objects.filter(category=family)
        self.assertEqual(topics.count(), len(FAMILY_TOPICS))
        self.assertEqual(topics.count(), topics.values("slug").distinct().count())
        for slug in REQUIRED_FAMILY_SLUGS:
            self.assertTrue(topics.filter(slug=slug, is_active=True).exists(), slug)
        contents = LegalContent.objects.filter(
            topic__category=family,
            language__code="en",
            verification_status="VERIFIED",
        )
        self.assertEqual(contents.count(), len(FAMILY_TOPICS))
        for content in contents:
            self.assertTrue(content.source_id)
            self.assertTrue(content.legal_reference)
            self.assertTrue(content.next_steps)
            self.assertTrue(content.summary)
            self.assertTrue(content.disclaimer)

    def test_family_sources_exist(self):
        for source in FAMILY_SOURCES:
            self.assertTrue(
                LegalSource.objects.filter(name=source["name"]).exists(),
                source["name"],
            )

    def test_i18n_covers_every_family_topic(self):
        slugs = {topic["slug"] for topic in FAMILY_TOPICS}
        self.assertEqual(slugs, set(FAMILY_TOPIC_I18N))

    def test_complete_fields_translated_for_seed_languages(self):
        family = LegalCategory.objects.get(slug="family")
        self.assertEqual(_translation(family, "lg", "name").text, "Amaka")
        self.assertEqual(_translation(family, "teo", "name").text, "Auren")
        self.assertEqual(_translation(family, "ach", "name").text, "Gang")

        topic = LegalTopic.objects.get(slug="family-child-maintenance")
        content = LegalContent.objects.get(topic=topic, language__code="en")
        for lang in ("lg", "teo", "ach"):
            packed = translation_fields_for_topic(topic.slug, lang)
            self.assertEqual(_translation(topic, lang, "name").text, packed["name"])
            for field in CONTENT_FIELDS:
                row = _translation(content, lang, field)
                self.assertIsNotNone(row, f"{lang}.{field}")
                self.assertEqual(row.text, packed[field])
                self.assertTrue(row.is_verified)
                self.assertNotEqual(row.text, getattr(content, field))

    def test_setup_does_not_overwrite_admin_edits(self):
        topic = LegalTopic.objects.get(slug="family-child-maintenance")
        content = LegalContent.objects.get(topic=topic, language__code="en")
        content.summary = "ADMIN EDIT — do not replace"
        content.save(update_fields=["summary", "updated_at"])
        lg_row = _translation(content, "lg", "summary")
        lg_row.text = "ADMIN LG EDIT"
        lg_row.save(update_fields=["text", "updated_at"])

        call_command("setup_manya")

        content.refresh_from_db()
        self.assertEqual(content.summary, "ADMIN EDIT — do not replace")
        lg_row.refresh_from_db()
        self.assertEqual(lg_row.text, "ADMIN LG EDIT")
        self.assertEqual(LegalTopic.objects.filter(slug="family-child-maintenance").count(), 1)
        self.assertEqual(LegalCategory.objects.filter(slug="family").count(), 1)


class FamilyTranslationFallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_manya")

    def test_database_translation_used_before_sunbird(self):
        topic = LegalTopic.objects.get(slug="family-child-maintenance")
        content = LegalContent.objects.get(topic=topic, language__code="en")
        with SUNBIRD_ON:
            with (
                patch.object(
                    SunbirdTranslationService, "is_supported", return_value=True
                ),
                patch.object(
                    SunbirdTranslationService,
                    "translate",
                    side_effect=AssertionError("must not call Sunbird"),
                ),
            ):
                self.assertEqual(
                    TranslationService.get_content(content, "title", "lg"),
                    translation_fields_for_topic(topic.slug, "lg")["title"],
                )

    def test_sunbird_used_when_database_translation_missing(self):
        topic = LegalTopic.objects.get(slug="family-child-maintenance")
        content = LegalContent.objects.get(topic=topic, language__code="en")
        ContentTranslation.objects.filter(
            content_type=ContentType.objects.get_for_model(content),
            object_id=content.pk,
            field="title",
            language__code="lg",
        ).delete()
        with SUNBIRD_ON:
            with (
                patch.object(
                    SunbirdTranslationService, "is_supported", return_value=True
                ),
                patch.object(
                    SunbirdTranslationService, "translate", return_value="SUNBIRD TITLE"
                ) as sb,
            ):
                self.assertEqual(
                    TranslationService.get_content(content, "title", "lg"),
                    "SUNBIRD TITLE",
                )
                sb.assert_called_once()
        row = _translation(content, "lg", "title")
        self.assertEqual(row.text, "SUNBIRD TITLE")
        self.assertEqual(row.translation_source, "sunbird")

    def test_sunbird_unavailable_falls_back_to_english(self):
        topic = LegalTopic.objects.get(slug="family-child-maintenance")
        content = LegalContent.objects.get(topic=topic, language__code="en")
        ContentTranslation.objects.filter(
            content_type=ContentType.objects.get_for_model(content),
            object_id=content.pk,
            field="summary",
            language__code="ach",
        ).delete()
        with SUNBIRD_ON:
            with (
                patch.object(
                    SunbirdTranslationService, "is_supported", return_value=True
                ),
                patch.object(SunbirdTranslationService, "translate", return_value=None),
            ):
                self.assertEqual(
                    TranslationService.get_content(content, "summary", "ach"),
                    content.summary,
                )

    def test_sunbird_does_not_overwrite_manual_translation(self):
        topic = LegalTopic.objects.get(slug="family-wills")
        content = LegalContent.objects.get(topic=topic, language__code="en")
        row = _translation(content, "lg", "title")
        original = row.text
        with SUNBIRD_ON:
            with (
                patch.object(
                    SunbirdTranslationService, "is_supported", return_value=True
                ),
                patch.object(
                    SunbirdTranslationService, "translate", return_value="WRONG"
                ),
            ):
                TranslationService.get_content(content, "title", "lg")
        row.refresh_from_db()
        self.assertEqual(row.text, original)
        self.assertEqual(row.translation_source, "manual")


class FamilyApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_manya")

    def setUp(self):
        self.client = APIClient()

    def test_categories_include_family_by_slug(self):
        resp = self.client.get("/api/legal/categories/")
        self.assertEqual(resp.status_code, 200)
        slugs = {item["slug"] for item in resp.json()}
        self.assertIn("family", slugs)

    def test_family_category_and_topics(self):
        resp = self.client.get("/api/legal/categories/family/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["slug"], "family")
        topic_slugs = {item["slug"] for item in data["topics"]}
        self.assertTrue(REQUIRED_FAMILY_SLUGS.issubset(topic_slugs))

    def test_family_content_translated_via_lang_query(self):
        resp = self.client.get(
            "/api/legal/topics/family-child-maintenance/?lang=lg"
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        packed = translation_fields_for_topic("family-child-maintenance", "lg")
        self.assertEqual(payload["name"], packed["name"])
        self.assertEqual(payload["content"]["title"], packed["title"])
        self.assertEqual(payload["content"]["summary"], packed["summary"])
        self.assertEqual(payload["content"]["next_steps"], packed["next_steps"])
        self.assertNotIn("Parents have a duty", payload["content"]["summary"])


class FamilyUssdSmsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_manya")

    def setUp(self):
        self.service = UssdService()

    def _call(self, text, session="fam"):
        return self.service.handle(
            {
                "sessionId": session,
                "phoneNumber": "+256700000099",
                "text": text,
            }
        )["response"]

    def _select_topic_named(self, session, current_path, current_resp, name_fragment):
        """Paginate the already-open topic list until ``name_fragment`` is visible."""
        path = current_path
        resp = current_resp
        for _ in range(15):
            for line in resp.splitlines():
                if name_fragment in line and line[:1].isdigit() and ". " in line:
                    choice = line.split(".", 1)[0].strip()
                    next_path = f"{path}*{choice}"
                    return self._call(next_path, session=session), next_path
            if "\n9. " in resp:
                path = f"{path}*9"
                resp = self._call(path, session=session)
                continue
            self.fail(f"Topic containing {name_fragment!r} not found in:\n{resp}")
        self.fail(f"Gave up paginating for {name_fragment!r}")

    def _family_child_maintenance_journey(self, lang_digit, session, name_fragment):
        self._call("", session=session)
        main = self._call(lang_digit, session=session)
        cats = self._call(f"{lang_digit}*2", session=session)
        issues = self._call(f"{lang_digit}*2*3", session=session)
        options, path = self._select_topic_named(
            session, f"{lang_digit}*2*3", issues, name_fragment
        )
        rights = self._call(f"{path}*1", session=session)
        steps = self._call(f"{path}*2", session=session)
        return main, cats, options, rights, steps, path

    def test_english_know_my_rights_family_child_maintenance(self):
        main, cats, options, rights, steps, _path = self._family_child_maintenance_journey(
            "1", "en-fam", "Child maintenance"
        )
        self.assertIn("Know my rights", main)
        self.assertIn("Family", cats)
        self.assertIn("Child maintenance", options)
        self.assertIn("Children Act", rights)
        self.assertIn("probation", steps.lower())

    def test_luganda_family_child_maintenance_fully_translated(self):
        packed = translation_fields_for_topic("family-child-maintenance", "lg")
        main, cats, options, rights, steps, path = self._family_child_maintenance_journey(
            "2", "lg-fam", packed["name"]
        )
        self.assertIn("Manya obuyinza bwo", main)
        self.assertIn("Amaka", cats)
        self.assertNotIn("Family", cats)
        self.assertIn(packed["name"], options)
        self.assertNotIn("Child maintenance", options)
        self.assertIn(packed["rights_information"][:40], rights)
        self.assertIn(packed["next_steps"][:40], steps)
        self.assertNotIn("Parents have a duty", rights)
        self.assertNotIn("If a parent fails", steps)

        with patch("apps.ussd.services.ussd_service.send_infosms") as sms:
            sms_resp = self._call(f"{path}*5", session="lg-fam")
        self.assertTrue(sms_resp.startswith("END "))
        body = sms.call_args.kwargs["message"]
        self.assertIn(packed["title"], body)
        self.assertIn(packed["summary"][:40], body)
        self.assertIn("Ekiddako", body)
        self.assertNotIn("Next step:", body)
        self.assertNotIn("This is general legal information, not legal advice.", body)

    def test_ateso_and_acholi_family_content_translated(self):
        for lang_digit, code, session in (("3", "teo", "teo-fam"), ("4", "ach", "ach-fam")):
            packed = translation_fields_for_topic("family-child-maintenance", code)
            _main, cats, options, rights, steps, _path = self._family_child_maintenance_journey(
                lang_digit, session, packed["name"]
            )
            self.assertIn(packed["name"], options)
            self.assertIn(packed["rights_information"][:30], rights)
            self.assertIn(packed["next_steps"][:30], steps)
            self.assertNotIn("Child maintenance", options)
            if code == "teo":
                self.assertIn("Auren", cats)
            else:
                self.assertIn("Gang", cats)

    def test_sms_api_uses_selected_language(self):
        packed = translation_fields_for_topic("family-child-maintenance", "lg")
        client = APIClient()
        with patch(
            "apps.messaging.views.SMSService.send", return_value={"ok": True}
        ) as send:
            resp = client.post(
                "/api/sms/",
                {
                    "phone_number": "+256700000099",
                    "topic": "family-child-maintenance",
                    "language": "lg",
                },
                format="json",
            )
        self.assertEqual(resp.status_code, 200)
        message = send.call_args.args[1]
        self.assertIn(packed["title"], message)
        self.assertIn(packed["summary"][:40], message)
        self.assertIn("Ekiddako", message)
        self.assertNotIn("Parents have a duty", message)
