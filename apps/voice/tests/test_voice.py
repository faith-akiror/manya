"""Tests for the Africa's Talking Voice IVR flow.

No real Africa's Talking or Sunbird traffic: the state machine runs against
the test database and the SMS sender is patched, exactly like the USSD and
two-way SMS suites.
"""

import json
from unittest.mock import patch

from django.test import TestCase

from apps.ussd.tests.test_ussd import seed_basic
from apps.voice.services.africastalking_voice import VoiceService
from apps.voice.services.voice_service import (
    VoiceConversationService,
    _normalize_digits,
)

CALLBACK_URL = "/api/voice/"
PHONE = "+256700000123"
SESSION = "ATVOID-000000001"


def voice_payload(session=SESSION, phone=PHONE, digits="", is_active="1", **extra):
    payload = {
        "sessionId": session,
        "isActive": is_active,
        "callerNumber": phone,
        "destinationNumber": "+256700000999",
        "direction": "inbound",
        "dtmfDigits": digits,
    }
    payload.update(extra)
    return payload


class VoiceXmlTests(TestCase):
    def test_say_escapes_special_characters(self):
        xml = VoiceService().say('Rights & duties < "quoted" >')
        self.assertIn("&amp;", xml)
        self.assertIn("&lt;", xml)
        self.assertIn("&gt;", xml)
        self.assertNotIn('"quoted"', xml)  # quotes are escaped as &quot;

    def test_end_response_closes_call(self):
        self.assertEqual(VoiceService().end_response(), "<Response/>")
        xml = VoiceService().end_response("Goodbye")
        self.assertIn("<Say", xml)
        self.assertNotIn("<GetDigits", xml)

    def test_continue_response_has_digits_and_callback(self):
        xml = VoiceService().continue_response(
            "Choose", "Press a number", callback_url="https://x.example/api/voice/"
        )
        self.assertIn("<GetDigits", xml)
        self.assertIn('callbackUrl="https://x.example/api/voice/"', xml)
        self.assertIn('numDigits="1"', xml)

    def test_normalize_digits_keeps_last_pressed(self):
        self.assertEqual(_normalize_digits(""), "")
        self.assertEqual(_normalize_digits("1"), "1")
        self.assertEqual(_normalize_digits("12"), "2")
        self.assertEqual(_normalize_digits("#4"), "4")


class VoiceFlowTests(TestCase):
    def setUp(self):
        seed_basic()
        self.service = VoiceConversationService()

    def _xml(self, payload):
        return self.service.dispatch(payload)["xml"]

    def test_initial_call_speaks_language_menu(self):
        xml = self._xml(voice_payload(digits=""))
        self.assertIn("<Response>", xml)
        self.assertIn("<Say", xml)
        self.assertIn("<GetDigits", xml)
        self.assertIn("Choose your language", xml)
        self.assertIn("English", xml)

    def test_select_language_reaches_main_menu(self):
        self._xml(voice_payload(digits=""))
        xml = self._xml(voice_payload(digits="1"))
        self.assertIn("<GetDigits", xml)
        self.assertIn("I have a problem", xml)

    def test_full_flow_to_rights(self):
        self._xml(voice_payload(digits=""))
        self._xml(voice_payload(digits="1"))  # English -> main menu
        self._xml(voice_payload(digits="1"))  # I have a problem -> categories
        self._xml(voice_payload(digits="1"))  # Employment -> issues
        self._xml(voice_payload(digits="1"))  # Unpaid salary -> topic options
        xml = self._xml(voice_payload(digits="1"))  # Understand my rights
        self.assertIn("satisfactory, fair and healthy conditions", xml)
        # Info screens still invite navigation (repeat / back).
        self.assertIn("Press 1 to hear this again", xml)

    def test_full_flow_to_next_steps(self):
        self._xml(voice_payload(digits=""))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        xml = self._xml(voice_payload(digits="2"))  # What should I do?
        self.assertIn("Gather documents", xml)

    def test_full_flow_to_documents(self):
        self._xml(voice_payload(digits=""))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        xml = self._xml(voice_payload(digits="3"))  # Documents I need
        self.assertIn("Contract, payslips", xml)

    def test_invalid_choice_reprompts(self):
        self._xml(voice_payload(digits=""))
        xml = self._xml(voice_payload(digits="9"))
        self.assertIn("Invalid choice", xml)
        self.assertIn("<GetDigits", xml)

    def test_final_notification_ends_call(self):
        xml = self._xml(voice_payload(is_active="0", digits="1"))
        self.assertIn("<Response", xml)
        self.assertNotIn("<Say", xml)

    def test_missing_session_id_is_safe(self):
        xml = self._xml(voice_payload(session=""))
        self.assertIn("<Say", xml)

    def test_missing_content_shows_friendly_message(self):
        from apps.legal.models import LegalCategory, LegalTopic

        cat = LegalCategory.objects.create(name="Land", slug="land", display_order=2)
        LegalTopic.objects.create(name="Tenancy", slug="tenancy", category=cat)
        self._xml(voice_payload(digits=""))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="2"))  # Land
        self._xml(voice_payload(digits="1"))  # Tenancy -> options
        xml = self._xml(voice_payload(digits="1"))  # rights are missing
        self.assertIn("not yet available", xml)
        self.assertNotIn("Traceback", xml)

    def test_send_sms_from_voice(self):
        with patch(
            "apps.ussd.services.ussd_service.send_infosms", return_value=[{"ok": True}]
        ) as mock_send:
            self._xml(voice_payload(digits=""))
            self._xml(voice_payload(digits="1"))
            self._xml(voice_payload(digits="1"))
            self._xml(voice_payload(digits="1"))
            self._xml(voice_payload(digits="1"))
            xml = self._xml(voice_payload(digits="5"))  # Send SMS
            self.assertIn("sent the information", xml)
            self.assertNotIn("<GetDigits", xml)
            mock_send.assert_called_once()

    def test_listen_replays_topic_options_on_voice(self):
        self._xml(voice_payload(digits=""))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        self._xml(voice_payload(digits="1"))
        xml = self._xml(voice_payload(digits="6"))  # Listen replays the options
        self.assertIn("<GetDigits", xml)
        self.assertIn("Understand my rights", xml)
        self.assertNotIn("coming soon", xml)


class VoiceEndpointTests(TestCase):
    def setUp(self):
        seed_basic()

    def test_form_payload_endpoint(self):
        response = self.client.post(CALLBACK_URL, data=voice_payload())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/xml"))
        self.assertIn(b"<GetDigits", response.content)
        self.assertIn(b"Choose your language", response.content)

    def test_json_payload_endpoint(self):
        response = self.client.post(
            CALLBACK_URL,
            data=json.dumps(voice_payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<GetDigits", response.content)

    def test_provider_failure_ends_call_cleanly(self):
        with patch(
            "apps.voice.views.VoiceConversationService.dispatch",
            side_effect=Exception("boom"),
        ):
            response = self.client.post(CALLBACK_URL, data=voice_payload())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<Response>", response.content)
        self.assertNotIn(b"Traceback", response.content)

    def test_empty_payload_is_tolerated(self):
        # Matches the channel smoke test: POST {} still returns a clean 200.
        response = self.client.post(
            CALLBACK_URL, data={}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<Response", response.content)
        self.assertIn(b"<Say", response.content)
        self.assertNotIn(b"<GetDigits", response.content)
