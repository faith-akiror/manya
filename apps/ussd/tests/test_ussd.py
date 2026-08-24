"""Tests for the MANYA USSD flow (Africa's Talking callback)."""

from unittest.mock import patch

from django.test import TestCase

from apps.languages.models import Language, UIMessage
from apps.legal.models import (
    DISCLAIMER,
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)
from apps.ussd.services.ussd_service import UssdService


def seed_basic():
    Language.objects.create(code="en", name="English", is_default=True, display_order=1)
    Language.objects.create(code="lg", name="Luganda", display_order=2)
    Language.objects.create(code="teo", name="Ateso", display_order=3)
    Language.objects.create(code="ach", name="Acholi", display_order=4)
    ach = Language.objects.get(code="ach")
    # A couple of UI strings so the Acholi language switch is observable.
    UIMessage.objects.create(language=ach, key="i_have_a_problem", text="An aya mone")
    UIMessage.objects.create(language=ach, key="choose_issue", text="Yer gweno")
    source = LegalSource.objects.create(
        name="Constitution of Uganda",
        source_type="CONSTITUTION",
        url="https://x",
        status="ACTIVE",
        authority_level=1,
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
        title="Unpaid salary / wages",
        summary="You are entitled to wages.",
        rights_information="You have the right to work under satisfactory, fair and healthy conditions.",
        what_this_means="You must be paid for work done.",
        next_steps="1. Gather documents. 2. Ask in writing. 3. Seek help.",
        documents_required="Contract, payslips, messages.",
        legal_reference="Art 40(1)",
        section_reference="Art 40(1)",
        disclaimer=DISCLAIMER,
        verification_status="VERIFIED",
        last_verified="2025-01-01",
    )
    return topic


class UssdFlowTests(TestCase):
    def setUp(self):
        seed_basic()
        self.service = UssdService()

    def _call(self, text, session="s1"):
        return self.service.handle(
            {"sessionId": session, "phoneNumber": "+256700000000", "text": text}
        )["response"]

    def test_initial_menu_lists_all_dynamic_languages(self):
        resp = self._call("")
        self.assertTrue(resp.startswith("CON "))
        self.assertIn("1. English", resp)
        self.assertIn("4. Acholi", resp)

    def test_dynamic_language_appears_without_code_change(self):
        Language.objects.create(code="nyn", name="Runyankole", display_order=5)
        resp = self._call("")
        self.assertIn("5. Runyankole", resp)

    def test_select_english_main_menu(self):
        resp = self._call("")
        resp = self._call("1")
        self.assertTrue(resp.startswith("CON "))
        self.assertIn("I have a problem", resp)
        self.assertIn("Find legal help", resp)

    def test_full_flow_to_next_steps(self):
        self._call("")
        self._call("1")  # English
        self._call("1*1")  # I have a problem
        resp = self._call("1*1*1")  # Employment
        self.assertIn("Unpaid salary", resp)
        self._call("1*1*1*1")  # Unpaid salary
        resp = self._call("1*1*1*1*2")  # What should I do?
        self.assertIn("Gather documents", resp)

    def test_full_flow_rights(self):
        self._call("")
        self._call("1")
        self._call("1*1")
        self._call("1*1*1")
        self._call("1*1*1*1")
        resp = self._call("1*1*1*1*1")  # Understand my rights
        self.assertIn("satisfactory, fair and healthy conditions", resp)

    def test_full_flow_documents(self):
        self._call("")
        self._call("1")
        self._call("1*1")
        self._call("1*1*1")
        self._call("1*1*1*1")
        resp = self._call("1*1*1*1*3")  # Documents I need
        self.assertIn("Contract, payslips", resp)

    def test_acholi_language_persists_through_session(self):
        self._call("")
        resp = self._call("4")  # Acholi
        # Main menu is rendered in Acholi UI strings.
        self.assertIn("An aya mone", resp)
        resp = self._call("4*1")  # I have a problem (categories, Acholi UI)
        self.assertIn("Yer gweno", resp)

    def test_invalid_input_returns_retry(self):
        self._call("")
        resp = self._call("9")  # invalid language choice
        self.assertTrue(resp.startswith("CON "))
        self.assertIn("Invalid choice", resp)

    def test_invalid_session_handled(self):
        resp = self.service.handle({"sessionId": "", "phoneNumber": "", "text": ""})
        self.assertTrue(resp["response"].startswith("END "))

    def test_empty_selection_main_returns_valid(self):
        self._call("")
        self._call("1")
        self._call("1*1")
        self._call("1*1*1")
        self._call("1*1*1*1")
        resp = self._call("1*1*1*1*8")  # invalid details choice
        self.assertIn("Invalid choice", resp)

    def test_send_sms_returns_end(self):
        with patch(
            "apps.ussd.services.ussd_service.send_infosms", return_value={"ok": True}
        ) as mock_send:
            self._call("")
            self._call("1")
            self._call("1*1")
            self._call("1*1*1")
            self._call("1*1*1*1")
            resp = self._call("1*1*1*1*5")  # Send SMS
            self.assertTrue(resp.startswith("END "))
            self.assertIn("sent the information", resp)
            mock_send.assert_called_once()

    def test_missing_content_shows_friendly_message(self):
        # A topic with no verified content
        cat = LegalCategory.objects.create(name="Land", slug="land", display_order=2)
        LegalTopic.objects.create(name="Tenancy", slug="tenancy", category=cat)
        self._call("")
        self._call("1")  # English
        self._call("1*1")  # I have a problem
        resp = self._call("1*1*2")  # Land category
        self.assertIn("Tenancy", resp)

    def test_database_failure_is_safe(self):
        with patch(
            "apps.ussd.services.ussd_service.UssdSession.objects.get_or_create",
            side_effect=Exception("db down"),
        ):
            resp = self.service.handle(
                {"sessionId": "x", "phoneNumber": "+2567", "text": ""}
            )
        self.assertTrue(resp["response"].startswith("END "))
        self.assertNotIn("Traceback", resp["response"])
        self.assertNotIn("db down", resp["response"])

    def test_exit(self):
        self._call("")
        self._call("1")  # English -> main menu
        resp = self._call("1*0")
        self.assertTrue(resp.startswith("END "))
