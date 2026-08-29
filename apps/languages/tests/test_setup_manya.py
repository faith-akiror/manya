"""Tests for the MANYA production bootstrap command."""

from django.test import TestCase

from apps.languages.models import Language, UIMessage
from apps.legal.models import LegalCategory, LegalContent, LegalSource, LegalTopic
from apps.policies.models import PolicyUpdate
from apps.referrals.models import Referral
from apps.ussd.services.ussd_service import UssdService


class SetupManyaTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command("setup_manya")

    def test_setup_manya_creates_languages(self):
        self.assertEqual(Language.objects.count(), 4)
        self.assertTrue(Language.objects.filter(code="en", is_default=True).exists())
        self.assertTrue(Language.objects.filter(code="lg", is_active=True).exists())
        self.assertTrue(Language.objects.filter(code="teo", is_active=True).exists())
        self.assertTrue(Language.objects.filter(code="ach", is_active=True).exists())

    def test_setup_manya_creates_ui_messages(self):
        en = Language.objects.get(code="en")
        self.assertEqual(UIMessage.objects.filter(language=en).count(), 27)
        self.assertTrue(UIMessage.objects.filter(language=en, key="welcome").exists())
        self.assertTrue(UIMessage.objects.filter(language=en, key="more").exists())

    def test_setup_manya_creates_legal_sources(self):
        self.assertTrue(
            LegalSource.objects.filter(name="Constitution of Uganda").exists()
        )
        self.assertTrue(
            LegalSource.objects.filter(name="Employment Act, 2006").exists()
        )

    def test_setup_manya_creates_legal_categories_and_topics(self):
        self.assertTrue(LegalCategory.objects.filter(slug="employment").exists())
        self.assertTrue(LegalCategory.objects.filter(slug="family", is_active=True).exists())
        self.assertTrue(LegalTopic.objects.filter(slug="unpaid-salary").exists())
        self.assertTrue(LegalTopic.objects.filter(slug="tenancy").exists())
        self.assertTrue(LegalTopic.objects.filter(slug="family-child-maintenance").exists())

    def test_setup_manya_creates_verified_legal_content(self):
        topic = LegalTopic.objects.get(slug="unpaid-salary")
        content = LegalContent.objects.filter(
            topic=topic, language__code="en", verification_status="VERIFIED"
        ).first()
        self.assertIsNotNone(content)
        self.assertIn("paid for work", content.rights_information)

    def test_setup_manya_creates_referrals(self):
        self.assertTrue(Referral.objects.filter(name="Legal Aid Board").exists())
        self.assertTrue(
            Referral.objects.filter(name="Uganda Law Society Pro Bono").exists()
        )

    def test_setup_manya_creates_policies(self):
        self.assertTrue(
            PolicyUpdate.objects.filter(
                slug="minimum-wage-policy-2024", is_active=True
            ).exists()
        )

    def test_setup_manya_is_idempotent(self):
        from django.core.management import call_command

        call_command("setup_manya")
        call_command("setup_manya")

        self.assertEqual(Language.objects.count(), 4)
        self.assertEqual(UIMessage.objects.count(), 108)
        self.assertEqual(LegalSource.objects.count(), 10)
        self.assertEqual(LegalCategory.objects.count(), 3)
        self.assertEqual(LegalTopic.objects.count(), 47)
        self.assertEqual(Referral.objects.count(), 3)
        self.assertEqual(PolicyUpdate.objects.count(), 2)

    def test_ussd_full_flow_with_setup_data(self):
        service = UssdService()

        resp = service.handle(
            {"sessionId": "setup_test", "phoneNumber": "+256700000000", "text": ""}
        )["response"]
        self.assertTrue(resp.startswith("CON "))
        self.assertIn("Welcome to MANYA", resp)

        resp = service.handle(
            {"sessionId": "setup_test", "phoneNumber": "+256700000000", "text": "1"}
        )["response"]
        self.assertTrue(resp.startswith("CON "))
        self.assertIn("I have a problem", resp)

        resp = service.handle(
            {"sessionId": "setup_test", "phoneNumber": "+256700000000", "text": "1*1"}
        )["response"]
        self.assertIn("Employment", resp)

        resp = service.handle(
            {"sessionId": "setup_test", "phoneNumber": "+256700000000", "text": "1*1*1"}
        )["response"]
        self.assertIn("Unpaid salary", resp)

        resp = service.handle(
            {
                "sessionId": "setup_test",
                "phoneNumber": "+256700000000",
                "text": "1*1*1*1",
            }
        )["response"]
        self.assertIn("Understand my rights", resp)

        resp = service.handle(
            {
                "sessionId": "setup_test",
                "phoneNumber": "+256700000000",
                "text": "1*1*1*1*1",
            }
        )["response"]
        self.assertIn("paid for work", resp)

    def test_new_language_auto_creates_ui_templates(self):
        sw = Language.objects.create(
            code="sw",
            name="Swahili",
            native_name="Kiswahili",
            is_active=True,
            display_order=5,
        )

        self.assertEqual(
            UIMessage.objects.filter(language=sw, key="welcome").count(), 1
        )
        self.assertEqual(
            UIMessage.objects.filter(language=sw, key="i_have_a_problem").count(), 1
        )
        self.assertEqual(UIMessage.objects.filter(language=sw).count(), 27)
