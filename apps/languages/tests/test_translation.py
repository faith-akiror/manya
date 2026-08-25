"""Tests proving the Sunbird-powered translation service is actually used.

The Sunbird HTTP request itself is mocked — tests patch the production class
``apps.languages.services.sunbird_translation.SunbirdTranslationService``, so
no real network call or API key is involved.
"""

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from apps.languages.models import (
    ContentTranslation,
    Language,
    Translation,
    UIMessage,
)
from apps.languages.services.sunbird_translation import SunbirdTranslationService
from apps.languages.services.translation_service import TranslationService
from apps.ussd.services.ussd_service import UssdService
from apps.ussd.tests.test_ussd import seed_basic

# Deterministic "machine translations" returned by the fake provider for the
# exact English strings used by the seeded test data.
LUGANDA_MAP = {
    "Welcome to MANYA": "LUG_WELCOME",
    "I have a problem": "LUG_PROBLEM",
    "Know my rights": "LUG_KNOW_RIGHTS",
    "Find legal help": "LUG_FIND_HELP",
    "Policy Updates": "LUG_POLICY",
    "Change Language": "LUG_CHANGE_LANG",
    "Choose your issue": "LUG_CHOOSE_ISSUE",
    "Employment": "Emirimu",
    "Land": "Ettaka",
    "Family": "Amaka",
    "Unpaid salary": "Omusaalo ogusasulwa",
    ("You have the right to work under satisfactory, fair and "
     "healthy conditions."): "LUG_RIGHTS_TEXT",
    "1. Gather documents. 2. Ask in writing. 3. Seek help.": "LUG_STEPS",
    "Contract, payslips, messages.": "LUG_DOCS",
}

SUNBIRD_ON = override_settings(SUNBIRD_ENABLED=True, SUNBIRD_API_TOKEN="fake-token")


def fake_translate(text, source_language, target_language):
    """Deterministic fake provider replacing the real Sunbird API call."""
    return LUGANDA_MAP.get((text or "").strip(), "TRANS:" + text)


def first_category():
    from apps.legal.models import LegalCategory

    return LegalCategory.objects.first()


def make_translation(obj, lang_code, field, text, **overrides):
    lang = Language.objects.get(code=lang_code)
    defaults = dict(
        language=lang,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        field=field,
        text=text,
        is_verified=True,
        translation_source="manual",
        translation_status="reviewed",
    )
    defaults.update(overrides)
    return ContentTranslation.objects.create(**defaults)


class SunbirdServiceTests(TestCase):
    """Prove database-first, Sunbird-on-miss, save-and-reuse semantics."""

    def setUp(self):
        seed_basic()

    def test_existing_verified_translation_never_calls_sunbird(self):
        cat = first_category()
        make_translation(cat, "lg", "name", "Emirimu ebyafaayo")
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService,
                "translate",
                side_effect=AssertionError("must not call Sunbird"),
            ) as sb:
                result = TranslationService.get_content(cat, "name", "lg")
                self.assertEqual(result, "Emirimu ebyafaayo")
                sb.assert_not_called()

    def test_missing_translation_calls_sunbird_saves_and_reuses(self):
        cat = first_category()
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", side_effect=fake_translate
            ) as sb:
                self.assertEqual(
                    TranslationService.get_content(cat, "name", "lg"), "Emirimu"
                )
                self.assertEqual(sb.call_count, 1)

                row = ContentTranslation.objects.get(
                    language__code="lg",
                    content_type__model="legalcategory",
                    object_id=cat.pk,
                    field="name",
                )
                self.assertEqual(row.text, "Emirimu")
                self.assertFalse(row.is_verified)
                self.assertEqual(row.translation_source, "sunbird")
                self.assertEqual(row.translation_status, "machine_translated")

                # Second request reads the saved row; no new Sunbird call.
                self.assertEqual(
                    TranslationService.get_content(cat, "name", "lg"), "Emirimu"
                )
                self.assertEqual(sb.call_count, 1)

    def test_sunbird_failure_falls_back_to_english(self):
        cat = first_category()
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(SunbirdTranslationService, "translate", return_value=None):
                result = TranslationService.get_content(cat, "name", "lg")
                self.assertEqual(result, "Employment")
        self.assertFalse(
            ContentTranslation.objects.filter(
                language__code="lg", object_id=cat.pk
            ).exists()
        )

    def test_unsupported_language_skips_sunbird_and_falls_back(self):
        Language.objects.create(code="fr", name="French", is_active=True)
        cat = first_category()
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=False
            ), patch.object(
                SunbirdTranslationService,
                "translate",
                side_effect=AssertionError("must not call"),
            ) as sb:
                self.assertEqual(
                    TranslationService.get_content(cat, "name", "fr"), "Employment"
                )
                sb.assert_not_called()

    def test_reviewed_manual_translation_never_overwritten(self):
        cat = first_category()
        make_translation(cat, "lg", "name", "Emirimu (human reviewed)")
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", return_value="WRONG"
            ) as sb:
                result = TranslationService.get_content(cat, "name", "lg")
                self.assertEqual(result, "Emirimu (human reviewed)")
                sb.assert_not_called()

    def test_free_text_translation_cache(self):
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", side_effect=fake_translate
            ) as sb:
                first = TranslationService.translate("Unpaid salary", "lg")
                self.assertTrue(first)
                self.assertEqual(Translation.objects.count(), 1)
                self.assertEqual(
                    TranslationService.translate("Unpaid salary", "lg"), first
                )
                self.assertEqual(sb.call_count, 1)

    def test_disabled_provider_returns_source_and_saves_nothing(self):
        with override_settings(SUNBIRD_ENABLED=False, SUNBIRD_API_TOKEN=""):
            self.assertEqual(TranslationService.translate("Hello", "lg"), "Hello")
            self.assertFalse(Translation.objects.exists())

    def test_new_language_automatically_machine_translated(self):
        sw = Language.objects.create(
            code="sw", name="Swahili", native_name="Kiswahili", is_active=True
        )
        cat = first_category()
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", return_value="Kazi"
            ):
                self.assertEqual(
                    TranslationService.get_content(cat, "name", "sw"), "Kazi"
                )
        row = ContentTranslation.objects.get(
            language=sw, object_id=cat.pk, field="name"
        )
        self.assertEqual(row.text, "Kazi")
        self.assertEqual(row.translation_source, "sunbird")

    def test_ui_message_get_text_translates_and_persists(self):
        lg = Language.objects.get(code="lg")
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", side_effect=fake_translate
            ) as sb:
                self.assertEqual(
                    TranslationService.get_text("welcome", "lg"), "LUG_WELCOME"
                )
                self.assertTrue(
                    UIMessage.objects.filter(language=lg, key="welcome").exists()
                )
                self.assertEqual(
                    TranslationService.get_text("welcome", "lg"), "LUG_WELCOME"
                )
                self.assertEqual(sb.call_count, 1)

    def test_generate_missing_is_idempotent(self):
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", side_effect=fake_translate
            ):
                first = TranslationService.generate_missing_for_language(
                    "lg", include_ui=False
                )
                self.assertGreater(first["created"], 0)
                self.assertEqual(first["failed"], 0)
                second = TranslationService.generate_missing_for_language(
                    "lg", include_ui=False
                )
                self.assertEqual(second["created"], 0)
                self.assertGreater(second["skipped"], 0)

    def test_facade_maps_codes_and_calls_http_client(self):
        with SUNBIRD_ON:
            provider = SunbirdTranslationService()
            with patch.object(
                provider._http, "translate", return_value="Emirimu"
            ) as http, patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ):
                result = provider.translate("Original", "en", "lg")
                self.assertEqual(result, "Emirimu")
                http.assert_called_once()
                self.assertEqual(http.call_args.kwargs["target_language"], "lug")
                self.assertEqual(http.call_args.kwargs["source_language"], "eng")

    def test_code_mapping(self):
        from apps.languages.services.sunbird_translation import (
            from_sunbird_code,
            to_sunbird_code,
        )

        self.assertEqual(to_sunbird_code("lg"), "lug")
        self.assertEqual(to_sunbird_code("en"), "eng")
        self.assertEqual(to_sunbird_code("ach"), "ach")
        self.assertEqual(from_sunbird_code("lug"), "lg")
class UssdSunbirdFlowTests(TestCase):
    """Full USSD navigation in Luganda — legal content comes from Sunbird."""

    def setUp(self):
        seed_basic()
        self.service = UssdService()

    def _call(self, text, session="lg1"):
        return self.service.handle(
            {
                "sessionId": session,
                "phoneNumber": "+256700000001",
                "text": text,
            }
        )["response"]

    def test_luganda_flow_menu_and_legal_content_translated(self):
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", side_effect=fake_translate
            ) as sb:
                self._call("", session="sess")
                main = self._call("2", session="sess")  # Luganda
                self.assertIn("LUG_PROBLEM", main)

                cats = self._call("2*1", session="sess")  # categories
                self.assertIn("Emirimu", cats)
                self.assertNotIn("Employment", cats)

                issues = self._call("2*1*1", session="sess")  # topics
                self.assertIn("Omusaalo ogusasulwa", issues)
                self.assertNotIn("Unpaid salary", issues)

                self._call("2*1*1*1", session="sess")  # topic options
                rights = self._call("2*1*1*1*1", session="sess")  # rights
                self.assertIn("LUG_RIGHTS_TEXT", rights)
                self.assertNotIn("satisfactory, fair and healthy conditions", rights)

                calls_after_first = sb.call_count
                # Fresh session, same flow: cached in DB, no new Sunbird call.
                self.service = UssdService()
                self._call("", session="sess2")
                self._call("2", session="sess2")
                self._call("2*1", session="sess2")
                self._call("2*1*1", session="sess2")
                self._call("2*1*1*1", session="sess2")
                self._call("2*1*1*1*1", session="sess2")
                self.assertEqual(sb.call_count, calls_after_first)


class ApiTranslationTests(TestCase):
    """The public API resolves translations through the SAME translation service."""

    def setUp(self):
        from apps.legal.models import (
            LegalCategory,
            LegalContent,
            LegalSource,
            LegalTopic,
        )

        Language.objects.create(code="en", name="English", is_default=True)
        Language.objects.create(code="lg", name="Luganda")
        source = LegalSource.objects.create(
            name="Constitution of Uganda", source_type="CONSTITUTION", url="https://x"
        )
        category = LegalCategory.objects.create(name="Employment", slug="employment")
        topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=category
        )
        en = Language.objects.get(code="en")
        LegalContent.objects.create(
            topic=topic,
            language=en,
            source=source,
            title="Unpaid salary",
            summary="Summary.",
            rights_information="You have rights.",
            what_this_means="In simple terms.",
            next_steps="Seek help.",
            documents_required="Contract, payslips.",
            legal_reference="Article 40(1)",
            verification_status="VERIFIED",
            last_verified="2025-01-01",
        )

    def test_topic_detail_lang_uses_translation_service(self):
        from apps.legal.models import LegalContent

        legal_content = LegalContent.objects.first()
        make_translation(legal_content, "lg", "rights_information", "LUG_RIGHTS")
        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService, "translate", side_effect=fake_translate
            ) as sb:
                resp = self.client.get("/api/legal/topics/unpaid-salary/?lang=lg")
                self.assertEqual(resp.status_code, 200)
                data = resp.json()["content"]
                # Pre-translated (reviewed) value is used for rights.
                self.assertEqual(data["rights_information"], "LUG_RIGHTS")
                # Missing fields are machine-translated via the same service.
                self.assertEqual(data["title"], "Omusaalo ogusasulwa")
                # Sunbird is never called for the already-translated field.
                rights_text = "You have rights."
                self.assertNotIn(
                    rights_text,
                    [c.args[0] for c in sb.call_args_list],
                )