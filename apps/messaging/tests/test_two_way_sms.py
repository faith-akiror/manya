"""Tests for the two-way SMS system (incoming, replies, delivery reports).

No real Africa's Talking or Sunbird traffic: SMSService.send is patched and
the Sunbird facade is mocked, exactly like the USSD/translation suites.
"""

import json
import itertools
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.languages.models import Language, UIMessage
from apps.languages.services.sunbird_translation import SunbirdTranslationService
from apps.messaging.models import IncomingSMS, SmsDeliveryReport
from apps.messaging.services.africastalking_sms import (
    SMSService,
    split_sms_message,
)
from apps.ussd.models import UssdSession
from apps.ussd.tests.test_ussd import seed_basic

SUNBIRD_ON = override_settings(SUNBIRD_ENABLED=True, SUNBIRD_API_TOKEN="fake-token")

CALLBACK_URL = "/api/messaging/sms/callback/"
INCOMING_URL = "/api/messaging/sms/incoming/"
PHONE = "+256700000010"

_ids = itertools.count(1)


def _incoming_payload(text="1", phone=PHONE):
    return {
        "from": phone,
        "to": "20880",
        "text": text,
        "id": f"in-{next(_ids)}",
    }


def post_incoming(client, text="", phone=PHONE, raw=None):
    payload = raw if raw is not None else _incoming_payload(text, phone)
    return client.post(
        INCOMING_URL,
        data=json.dumps(payload),
        content_type="application/json",
    )


class SplitSmsMessageTests(TestCase):
    def test_short_message_single_part_no_header(self):
        self.assertEqual(split_sms_message("Hello from MANYA"), ["Hello from MANYA"])

    def test_long_message_splits_at_word_boundaries(self):
        text = " ".join(["employment"] * 60)  # ~610 chars
        parts = split_sms_message(text)
        self.assertGreater(len(parts), 1)
        for part in parts:
            body = part.split("\n", 1)[-1]
            # No word is ever cut in half.
            self.assertTrue(all(w == "employment" for w in body.split()))

    def test_parts_have_numbered_headers(self):
        parts = split_sms_message(" ".join(["rights"] * 80))
        self.assertGreater(len(parts), 1)
        total = len(parts)
        for i, part in enumerate(parts, start=1):
            self.assertIn(f"Part {i}/{total}", part)

    def test_no_words_lost_when_splitting(self):
        original = " ".join(["word"] * 200)
        parts = split_sms_message(original)
        rebuilt = "".join(
            p.split("\n", 1)[-1] if p.startswith("Part ") else p for p in parts
        )
        # Chunk boundaries consume one space; no letter may be lost or mangled.
        self.assertEqual(
            rebuilt.replace(" ", ""), original.replace(" ", "")
        )
        for part in parts:
            self.assertLessEqual(len(part), 160)

    def test_empty_text_returns_empty(self):
        self.assertEqual(split_sms_message("   "), [])

    def test_oversized_single_word_is_hard_cut(self):
        parts = split_sms_message("x" * 400)
        joined = "".join(p.replace("Part ", "").replace("/3\n", "") for p in parts)
class IncomingSMSTests(TestCase):
    """The full two-way journey over the incoming webhook."""

    def setUp(self):
        seed_basic()

    @staticmethod
    def _send(client, text="", phone=PHONE, raw=None):
        with patch.object(SMSService, "send", return_value={"ok": True}) as send:
            response = post_incoming(client, text=text, phone=phone, raw=raw)
        return response, send

    def test_first_message_starts_language_selection(self):
        response, send = self._send(self.client, text="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "processed"})

        session = UssdSession.objects.get(session_id=f"sms:{PHONE}")
        self.assertEqual(session.channel, "sms")
        self.assertEqual(session.menu, "start")

        incoming = IncomingSMS.objects.get(phone_number=PHONE)
        self.assertIn("Welcome to MANYA", incoming.reply_text)
        # The language list is rendered from the database.
        self.assertIn("2. Luganda", incoming.reply_text)
        send.assert_called_once()

    def test_language_selection_translates_and_persists(self):
        lg = Language.objects.get(code="lg")
        UIMessage.objects.create(
            language=lg, key="i_have_a_problem", text="Nina ekizibu"
        )

        with SUNBIRD_ON:
            with patch.object(
                SunbirdTranslationService, "is_supported", return_value=True
            ), patch.object(
                SunbirdTranslationService,
                "translate",
                side_effect=lambda text, src, tgt: "LUG:" + str(text),
            ):
                self._send(self.client, text="")
                self._send(self.client, text="2")  # Luganda

        session = UssdSession.objects.get(session_id=f"sms:{PHONE}")
        self.assertEqual(session.language_code, "lg")

        # The main-menu reply was translated via the central service.
        incoming = IncomingSMS.objects.order_by("-created_at").first()
        self.assertIn("LUG:", incoming.reply_text)

    def test_existing_session_continues_journey(self):
        self._send(self.client, text="")   # language menu
        self._send(self.client, text="1")  # English -> main menu
        session = UssdSession.objects.get(session_id=f"sms:{PHONE}")
        self.assertEqual(session.menu, "main")

        self._send(self.client, text="1")  # I have a problem
        session.refresh_from_db()
        self.assertEqual(session.menu, "categories")

        self._send(self.client, text="1")  # Employment -> topics
        session.refresh_from_db()
        self.assertEqual(session.menu, "issues")

    def test_legal_content_reaches_the_sms_user(self):
        self._send(self.client, text="")
        for _ in range(4):
            self._send(self.client, text="1")
        self._send(self.client, text="1")  # Understand my rights

        incoming = IncomingSMS.objects.order_by("-created_at").first()
        self.assertIn(
            "satisfactory, fair and healthy conditions", incoming.reply_text
        )
    def test_invalid_option_gets_error_reply_not_crash(self):
        self._send(self.client, text="")   # language menu
        self._send(self.client, text="1")  # English -> main menu
        self._send(self.client, text="98")  # invalid choice

        incoming = IncomingSMS.objects.order_by("-created_at").first()
        self.assertIn("Invalid choice", incoming.reply_text)

    def test_empty_message_still_replies_safely(self):
        response, _ = self._send(self.client, text="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(IncomingSMS.objects.count(), 1)
        incoming = IncomingSMS.objects.first()
        self.assertIn("Welcome to MANYA", incoming.reply_text)

    def test_duplicate_provider_retry_processed_once(self):
        payload = _incoming_payload(text="")
        with patch.object(SMSService, "send", return_value={"ok": True}):
            first = post_incoming(self.client, raw=payload)
            second = post_incoming(self.client, raw=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(IncomingSMS.objects.count(), 1)

    def test_invalid_phone_is_skipped_without_crash(self):
        response = post_incoming(
            self.client, raw={"from": "not-a-phone", "text": "hi"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(IncomingSMS.objects.count(), 0)

    def test_session_timeout_keeps_language_returns_to_main(self):
        lg = Language.objects.get(code="lg")
        UIMessage.objects.create(
            language=lg, key="choose_issue", text="Londa ekizibu"
        )
        UssdSession.objects.create(
            session_id=f"sms:{PHONE}",
            phone_number=PHONE,
            language_code="lg",
            menu="main",
            channel="sms",
        )
        UssdSession.objects.filter(session_id=f"sms:{PHONE}").update(
            updated_at=timezone.now() - timedelta(hours=25)
        )

        self._send(self.client, text="1")  # stale: resume at main -> problem
        session = UssdSession.objects.get(session_id=f"sms:{PHONE}")
        # Same language kept; journey resumed at the main menu.
        self.assertEqual(session.language_code, "lg")
        self.assertEqual(session.menu, "categories")

        incoming = IncomingSMS.objects.order_by("-created_at").first()
        self.assertIn("Londa ekizibu", incoming.reply_text)


class DeliveryReportTests(TestCase):
    def _post_callback(self, payload):
        return self.client.post(
            CALLBACK_URL, data=json.dumps(payload), content_type="application/json"
        )

    def test_successful_delivery_stored(self):
        resp = self._post_callback(
            {
                "id": "ATMsgId_1",
                "phoneNumber": "+256700000010",
                "status": "Success",
                "statusCode": 101,
            }
        )
        self.assertEqual(resp.status_code, 200)
        report = SmsDeliveryReport.objects.get(message_id="ATMsgId_1")
        self.assertEqual(report.status, "Success")
        self.assertEqual(report.phone_number, "+256700000010")

    def test_failed_delivery_keeps_failure_reason(self):
        self._post_callback(
            {
                "id": "ATMsgId_2",
                "phoneNumber": "+256700000010",
                "status": "Failed",
                "failureReason": "InvalidNumber",
            }
        )
        report = SmsDeliveryReport.objects.get(message_id="ATMsgId_2")
        self.assertEqual(report.status, "Failed")
        self.assertEqual(report.failure_reason, "InvalidNumber")

    def test_status_transition_updates_same_record(self):
        self._post_callback(
            {"id": "ATMsgId_3", "phoneNumber": PHONE, "status": "Sent"}
        )
        self._post_callback(
            {"id": "ATMsgId_3", "phoneNumber": PHONE, "status": "Success"}
        )
        self.assertEqual(
            SmsDeliveryReport.objects.filter(message_id="ATMsgId_3").count(), 1
        )
        self.assertEqual(
            SmsDeliveryReport.objects.get(message_id="ATMsgId_3").status,
            "Success",
        )

    def test_duplicate_identical_callback_creates_one_record(self):
        payload = {"id": "ATMsgId_4", "phoneNumber": PHONE, "status": "Success"}
        self._post_callback(payload)
        self._post_callback(payload)
        self.assertEqual(SmsDeliveryReport.objects.count(), 1)

    def test_malformed_payload_rejected_cleanly(self):
        response = self.client.post(
            CALLBACK_URL, data="not-json{", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SmsDeliveryReport.objects.count(), 0)

    def test_batch_list_payload_handled(self):
        resp = self._post_callback(
            [
                {"id": "A", "phoneNumber": PHONE, "status": "Success"},
                {"id": "B", "phoneNumber": "+256700000011", "status": "Failed"},
            ]
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(SmsDeliveryReport.objects.count(), 2)