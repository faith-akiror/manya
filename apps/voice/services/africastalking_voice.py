"""Africa's Talking Voice service (MVP abstraction).

Voice is scoped as P2. This service isolates provider integration so Voice can
never break the website, USSD or SMS. In MVP the service returns a plain-text
speech intent rendered by Africa's Talking Voice; it can be swapped for a full
call-session flow later without changing callers.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

SAFE_TEXT_RE = re.compile(r"[<>]+")


class VoiceConfigurationError(Exception):
    """Africa's Talking Voice credentials are missing."""


class VoiceServiceError(Exception):
    """Voice could not be rendered."""


class VoiceService:
    """Abstraction for Africa's Talking Voice / TTS intents."""

    def __init__(self, voice_number=None, api_key=None, environment=None):
        self.voice_number = voice_number or os.getenv("AFRICASTALKING_VOICE_NUMBER", "")
        self.api_key = api_key or os.getenv("AFRICASTALKING_API_KEY", "")
        environment = (
            environment or os.getenv("AFRICASTALKING_ENVIRONMENT", "sandbox")
        ).lower()
        self.environment = (
            environment if environment in ("production", "sandbox") else "sandbox"
        )

    def is_configured(self) -> bool:
        return bool(self.voice_number and self.api_key)

    def say(self, text, language_code="en", requester=None, **kwargs) -> str:
        """Return a Voice/Say intent for ``text`` (MVP plain-text response)."""
        if not (text or "").strip():
            raise VoiceServiceError("Cannot synthesise empty text.")
        safe = SAFE_TEXT_RE.sub("", (text or "")[:400])
        return safe

    def read_content(self, content, language=None, requester=None):
        """Synthesise a LegalContent (title + summary)."""
        text = f"{content.title}. {content.summary or ''}".strip()
        return self.say(
            text,
            language_code=(language or getattr(content.language, "code", "en")),
            requester=requester,
        )
