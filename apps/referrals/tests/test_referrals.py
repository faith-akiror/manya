"""Tests for referral + policy public APIs."""

import json

from django.test import TestCase

from apps.languages.models import Language
from apps.policies.models import PolicyUpdate
from apps.referrals.models import Referral


def seed_referral(language=None):
    ref = Referral.objects.create(
        name="Uganda Law Society Pro Bono",
        description="Free legal aid at the Law Society.",
        category="Employment",
        location="Kampala",
        phone="+256700000000",
        email="help@example.org",
        website="https://www.uls.or.ug",
        services="Legal advice, representation",
        is_verified=True,
        last_verified="2025-01-01",
    )
    if language:
        ref.languages.add(language)
    return ref


class ReferralAPITests(TestCase):
    def setUp(self):
        self.en = Language.objects.create(code="en", name="English", is_default=True)
        seed_referral(self.en)
        Referral.objects.create(
            name="Unverified NGO", category="Land", is_verified=False
        )

    def test_only_verified_referrals_are_public(self):
        response = self.client.get("/api/referrals/")
        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.json()]
        self.assertEqual(names, ["Uganda Law Society Pro Bono"])
        self.assertNotIn("Unverified NGO", names)

    def test_referral_filter_by_category(self):
        response = self.client.get("/api/referrals/?category=Employment")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_referral_filter_by_language(self):
        response = self.client.get("/api/referrals/?language=en")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        response = self.client.get("/api/referrals/?language=ach")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_referral_never_fabricates_empty_contact(self):
        Referral.objects.create(
            name="Verified No-Contact", category="X", is_verified=True
        )
        response = self.client.get("/api/referrals/")
        payload = response.json()
        self.assertTrue(all(("phone" in item) for item in payload))


class PolicyAPITests(TestCase):
    def setUp(self):
        PolicyUpdate.objects.create(
            title="New National Employment Policy",
            slug="national-employment-policy",
            summary="Policy summary.",
            source="Official Gazette",
            is_active=True,
            published_at="2025-06-01",
        )
        PolicyUpdate.objects.create(
            title="Inactive news",
            slug="inactive-news",
            summary="x",
            is_active=False,
        )

    def test_only_active_policies_are_public(self):
        response = self.client.get("/api/policies/")
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.json()]
        self.assertEqual(titles, ["New National Employment Policy"])

    def test_policy_detail(self):
        response = self.client.get("/api/policies/national-employment-policy/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "New National Employment Policy")

    def test_inactive_policy_detail_404(self):
        response = self.client.get("/api/policies/inactive-news/")
        self.assertEqual(response.status_code, 404)


class ChannelAPITests(TestCase):
    def test_openapi_schema_available(self):
        from django.test import Client

        client = Client()
        response = client.get("/api/schema/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertIn("MANYA API", payload["info"]["title"])

    def test_health(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_voice_endpoint(self):
        response = self.client.post(
            "/api/voice/", data={}, content_type="application/json"
        )
        self.assertIn(response.status_code, (200, 503))

    def test_sms_invalid_phone_rejected(self):
        response = self.client.post(
            "/api/sms/",
            data={"phone_number": "bad", "message": "hi"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_sms_missing_message_and_topic_rejected(self):
        response = self.client.post(
            "/api/sms/",
            data={"phone_number": "+256700000000"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
