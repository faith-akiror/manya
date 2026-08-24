"""Tests for the Africa's Talking SMS service abstraction."""

from unittest.mock import Mock, patch

from django.test import TestCase

from apps.messaging.services.africastalking_sms import (
    SMSService,
    SMSServiceError,
    build_content_sms,
    validate_phone_number,
)


def _mock_response(status_code=201, payload=None):
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=payload or {})
    return response


class SMSServiceTests(TestCase):
    def setUp(self):
        self.service = SMSService(
            username="u", api_key="k", environment="sandbox", shortcode="1234"
        )

    def test_is_configured(self):
        self.assertTrue(self.service.is_configured())

    def test_missing_credentials(self):
        svc = SMSService(username="", api_key="")
        self.assertFalse(svc.is_configured())

    def test_validate_phone_number(self):
        self.assertEqual(validate_phone_number("+256700000000"), "+256700000000")
        with self.assertRaises(SMSServiceError):
            validate_phone_number("not-a-phone")

    def test_send_success(self):
        payload = {"SMSMessageData": {"Recipients": [{"statusCode": 101}]}}
        with patch(
            "apps.messaging.services.africastalking_sms.requests.post",
            return_value=_mock_response(201, payload),
        ) as mock_post:
            response = self.service.send("+256700000000", "Test MANYA message")
            self.assertEqual(
                response["SMSMessageData"]["Recipients"][0]["statusCode"], 101
            )
            mock_post.assert_called_once()

    def test_send_invalid_number_raises(self):
        with self.assertRaises(SMSServiceError):
            self.service.send("bad", "msg")

    def test_send_provider_rejection(self):
        payload = {"SMSMessageData": {"Recipients": [{"statusCode": 404}]}}
        with patch(
            "apps.messaging.services.africastalking_sms.requests.post",
            return_value=_mock_response(201, payload),
        ):
            with self.assertRaises(SMSServiceError):
                self.service.send("+256700000000", "m")

    def test_send_api_failure_status(self):
        with patch(
            "apps.messaging.services.africastalking_sms.requests.post",
            return_value=_mock_response(500, {}),
        ):
            with self.assertRaises(SMSServiceError):
                self.service.send("+256700000000", "m")

    def test_timeout_is_isolated(self):
        import requests

        def boom(*args, **kwargs):
            raise requests.exceptions.Timeout()

        with patch(
            "apps.messaging.services.africastalking_sms.requests.post",
            side_effect=boom,
        ):
            with self.assertRaises(SMSServiceError):
                self.service.send("+256700000000", "m")

    def test_network_failure_isolated(self):
        with patch(
            "apps.messaging.services.africastalking_sms.requests.post",
            side_effect=Exception("network down"),
        ):
            with self.assertRaises(SMSServiceError):
                self.service.send("+256700000000", "m")

    def test_build_content_sms_contains_key_parts(self):
        from apps.languages.models import Language
        from apps.legal.models import (
            LegalCategory,
            LegalContent,
            LegalSource,
            LegalTopic,
        )

        cat = LegalCategory.objects.create(name="Employment", slug="employment")
        topic = LegalTopic.objects.create(
            name="Unpaid salary", slug="unpaid-salary", category=cat
        )
        content = LegalContent.objects.create(
            topic=topic,
            language=Language.objects.create(
                code="en", name="English", is_default=True
            ),
            source=LegalSource.objects.create(
                name="Constitution", source_type="CONSTITUTION"
            ),
            title="Unpaid salary",
            summary="Summary.",
            rights_information="R",
            what_this_means="W",
            next_steps="Seek help.",
            documents_required="D",
            legal_reference="Art 40(1)",
            verification_status="VERIFIED",
        )

        sms = build_content_sms(content)
        self.assertIn("Unpaid salary", sms)
        self.assertIn("Seek help.", sms)
        self.assertTrue(
            sms.endswith("This is general legal information, not legal advice.")
        )
