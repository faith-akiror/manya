"""Africa's Talking Voice renderer.

This module knows ONLY how to render Africa's Talking Voice XML intents
(``<Say>``, ``<GetDigits>``, ``<Response>``) and keeps provider details out of
the callback view and the state machine.

Africa's Talking Voice callback contract
(https://developers.africastalking.com/docs/voice/handle_calls):

* Africa's Talking POSTs call notifications to the registered callback URL
  with fields such as ``sessionId``, ``isActive``, ``callerNumber``,
  ``destinationNumber`` and ``dtmfDigits``.
* We answer 200 with XML. Actions run in order; only an input action
  (``<GetDigits>``) triggers the next notification.
* Returning ``<Response/>`` with no actions ends the call.

Text is rendered with the Google TTS voice from ``AFRICASTALKING_VOICE``
(default ``en-US-Standard-C``) and every string is XML-escaped.
"""

import logging
import os
import xml.sax.saxutils

logger = logging.getLogger(__name__)

DEFAULT_VOICE = os.getenv("AFRICASTALKING_VOICE", "en-US-Standard-C")


def xml_escape(text) -> str:
    """Escape text for XML text nodes / quoted attributes."""
    return xml.sax.saxutils.escape(str(text or ""), {'"': "&quot;"})


class VoiceServiceError(Exception):
    """A voice intent could not be rendered."""


class VoiceService:
    """Render Africa's Talking Voice XML intents (TTS + digit capture)."""

    def __init__(self, voice=None, timeout=12):
        self.voice = voice or DEFAULT_VOICE
        self.timeout = max(1, int(timeout or 12))

    def say(self, text) -> str:
        """``<Say>`` text-to-speech intent for ``text``."""
        if not str(text or "").strip():
            raise VoiceServiceError("Cannot synthesise empty text.")
        return f'<Say voice="{xml_escape(self.voice)}">{xml_escape(text)}</Say>'

    def get_digits(self, prompt, callback_url="") -> str:
        """``<GetDigits>`` captures a single key press from the caller.

        The ``callbackUrl`` falls back to the number's registered callback URL
        when omitted; we pass it explicitly so the flow survives dashboard
        re-configuration.
        """
        attributes = [
            f'timeout="{self.timeout}"',
            'numDigits="1"',
            'finishOnKey="#"',
        ]
        if callback_url:
            attributes.append(f'callbackUrl="{xml_escape(callback_url)}"')
        return f"<GetDigits {' '.join(attributes)}>{self.say(prompt)}</GetDigits>"

    def continue_response(self, text, prompt, callback_url="") -> str:
        """Speak ``text``, then listen for the caller's next digit."""
        return (
            f"<Response>{self.say(text)}"
            f"{self.get_digits(prompt, callback_url)}</Response>"
        )

    def end_response(self, text="") -> str:
        """End the call (an action-less ``<Response/>`` closes the session)."""
        if str(text or "").strip():
            return f"<Response>{self.say(text)}</Response>"
        return "<Response/>"
