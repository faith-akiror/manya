"""Tests for the public HTML dashboard."""

from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from apps.languages.models import ContentTranslation, Language
from apps.legal.models import LegalCategory, LegalContent, LegalSource, LegalTopic
from apps.messaging.models import IncomingSMS
from apps.ussd.models import UssdSession


class DashboardViewTests(TestCase):
    def setUp(self):
        self.en = Language.objects.create(
            code="en", name="English", native_name="English", is_default=True
        )
        self.lg = Language.objects.create(
            code="lg", name="Luganda", native_name="Luganda"
        )
        self.source = LegalSource.objects.create(
            name="Employment Act, 2006",
            organization="Parliament of Uganda",
            source_type="ACT",
            status="ACTIVE",
            authority_level=1,
            last_verified_at="2026-01-15T10:00:00Z",
            next_review_date=date(2026, 7, 15),
        )
        self.category = LegalCategory.objects.create(
            name="Employment", slug="employment"
        )
        self.topic = LegalTopic.objects.create(
            name="Unpaid salary",
            slug="unpaid-salary",
            category=self.category,
        )

    def test_empty_usage_shows_no_data_yet(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No data yet")
        self.assertContains(response, "no USSD or SMS conversations have been recorded")

    def test_active_languages_render_as_pills(self):
        Language.objects.create(
            code="ach", name="Acholi", native_name="Acholi", is_active=False
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Luganda")
        self.assertContains(response, "en")
        self.assertNotContains(response, "Acholi")

    def test_verified_topic_badge_and_languages(self):
        LegalContent.objects.create(
            topic=self.topic,
            language=self.en,
            source=self.source,
            title="Unpaid salary / wages",
            legal_reference="Art 40(1)",
            last_verified=date(2026, 1, 1),
            verification_status="VERIFIED",
        )
        LegalContent.objects.create(
            topic=self.topic,
            language=self.lg,
            title="Omusolo ogutali musasuddwa",
            verification_status="DRAFT",
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Unpaid salary / wages")
        self.assertContains(response, "Verified")
        self.assertContains(response, "English (en)")
        self.assertContains(response, "Luganda (lg)")

    def test_draft_only_badge_for_unverified_content(self):
        LegalContent.objects.create(
            topic=self.topic,
            language=self.lg,
            title="Draft Luganda article",
            verification_status="DRAFT",
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Draft only")
        self.assertContains(response, 'class="badge badge-draft"')
        self.assertNotContains(response, 'class="badge badge-verified"')

    def test_sunbird_translation_counts_as_draft_language(self):
        ContentTranslation.objects.create(
            language=self.lg,
            content_type=ContentType.objects.get_for_model(LegalTopic),
            object_id=self.topic.pk,
            field="name",
            text="Omusolo",
            translation_source="sunbird",
            is_verified=False,
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Draft only")
        self.assertContains(response, "Luganda (lg)")

    def test_sources_list_active_records(self):
        LegalSource.objects.create(
            name="Repealed ordinance",
            status="REPEALED",
            authority_level=3,
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Employment Act, 2006")
        self.assertContains(response, "Level 1")
        self.assertNotContains(response, "Repealed ordinance")

    def test_community_questions_count_real_session_selections(self):
        LegalTopic.objects.create(
            name="Wrongful termination",
            slug="wrongful-termination",
            category=self.category,
        )
        UssdSession.objects.create(
            session_id="at-1",
            phone_number="+256700000001",
            data={"user_selection": ["employment", "unpaid-salary"]},
            channel="ussd",
        )
        UssdSession.objects.create(
            session_id="at-2",
            phone_number="+256700000002",
            data={"user_selection": ["employment", "unpaid-salary"]},
            channel="ussd",
        )
        UssdSession.objects.create(
            session_id="sms:+256700000003",
            phone_number="+256700000003",
            data={"user_selection": ["employment", "wrongful-termination"]},
            channel="sms",
        )
        IncomingSMS.objects.create(
            phone_number="+256700000003",
            message_text="1",
            fingerprint="sms-fingerprint-1",
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "What people are asking about")
        self.assertContains(response, "Unpaid salary")
        self.assertContains(response, "2 sessions")
        self.assertContains(response, "Wrongful termination")
        self.assertContains(response, "1 session")
        html = response.content.decode()
        self.assertLess(html.find("2 sessions"), html.find("1 session"))
        self.assertNotContains(response, "No data yet")

    def test_incoming_sms_without_topic_does_not_invent_counts(self):
        IncomingSMS.objects.create(
            phone_number="+256700000009",
            message_text="hello",
            fingerprint="sms-fingerprint-empty",
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "nobody has selected a topic")
        self.assertContains(response, "1 inbound SMS")

    def test_succession_and_wills_section_renders_both_cards(self):
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Succession and Wills")
        self.assertContains(response, "Plan Your Succession")
        self.assertContains(response, "Start Your Will")
        self.assertContains(response, "https://will-generator.jessemwegs.dev/")
        self.assertContains(response, 'target="_blank"')
        self.assertContains(
            response,
            "MANYA does not store or see the information you enter there.",
        )
        self.assertContains(response, "What to do if a will is disputed or ignored")
        self.assertContains(response, "lodge a caveat at court before probate")
        self.assertContains(
            response,
            "Source: Succession Act, Cap 162, and the Succession (Amendment) Act 2022",
        )
        response = self.client.get("/dashboard/")
        self.assertContains(response, "Plan Your Succession")
        self.assertContains(response, "Start Your Will")
        self.assertContains(response, "https://will-generator.jessemwegs.dev/")
        self.assertContains(response, 'target="_blank"')
        self.assertContains(
            response,
            "MANYA does not store or see the information you enter there.",
        )
