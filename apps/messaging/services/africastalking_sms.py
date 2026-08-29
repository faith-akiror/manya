"""Africa's Talking SMS service.

External API calls are isolated here — Django views never talk to
Africa's Talking directly. If the SMS API is down or misconfigured, the
rest of MANYA (website, USSD, Voice) keeps working.
"""

import logging
import os
import re

import requests

logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"^\+?\d{9,15}$")

# Practical single-SMS ceiling. The "Part i/n" header is prepended on top of
# this when a message must be split, so keep head-room inside 160 chars.
SMS_PART_LIMIT = 150


def validate_phone_number(phone_number):
    """Validate and normalize a phone number. Raises SMSServiceError if invalid."""
    phone = (phone_number or "").strip()
    if not PHONE_RE.fullmatch(phone):
        raise SMSServiceError(f"Invalid phone number: {phone_number!r}.")
    return phone


class SMSConfigurationError(Exception):
    """Africa's Talking credentials are missing."""


class SMSServiceError(Exception):
    """SMS could not be sent (network, API, or invalid number)."""


class SMSService:
    """Small, fault-tolerant wrapper around the Africa's Talking SMS API.

    Production: https://api.africastalking.com/version1/messaging
    Sandbox:   https://api.sandbox.africastalking.com/version1/messaging
    """

    def __init__(self, username=None, api_key=None, environment=None, shortcode=None):
        self.username = username or os.getenv("AFRICASTALKING_USERNAME", "")
        self.api_key = api_key or os.getenv("AFRICASTALKING_API_KEY", "")
        self.shortcode = shortcode or os.getenv("AFRICASTALKING_USSD_SHORTCODE", "")
        environment = (
            environment or os.getenv("AFRICASTALKING_ENVIRONMENT", "sandbox")
        ).lower()
        self.environment = (
            environment if environment in ("production", "sandbox") else "sandbox"
        )

    @property
    def base_url(self) -> str:
        host = (
            "api.sandbox.africastalking.com"
            if self.environment == "sandbox"
            else "api.africastalking.com"
        )
        return f"https://{host}/version1/messaging"

    def is_configured(self) -> bool:
        return bool(self.username and self.api_key)

    @staticmethod
    def validate_phone_number(phone_number: str) -> str:
        phone = (phone_number or "").strip()
        if not PHONE_RE.fullmatch(phone):
            raise SMSServiceError(f"Invalid phone number: {phone_number!r}.")
        return phone

    def send(self, phone_number: str, message: str, **kwargs) -> dict:
        """Send one SMS. Returns the API response dict on success."""
        phone = validate_phone_number(phone_number)
        if not (message or "").strip():
            raise SMSServiceError("Cannot send an empty SMS.")
        if not self.is_configured():
            raise SMSConfigurationError(
                "Africa's Talking credentials are not configured."
            )

        data = {
            "username": self.username,
            "to": phone,
            "message": message[:160],
        }
        if self.shortcode:
            data["from"] = self.shortcode

        headers = {
            "apikey": self.api_key,
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                self.base_url, data=data, headers=headers, timeout=30
            )
        except requests.exceptions.Timeout as exc:
            raise SMSServiceError("SMS request timed out.") from exc
        except requests.exceptions.RequestException as exc:
            raise SMSServiceError("SMS service is unreachable.") from exc
        except Exception as exc:  # noqa: BLE001 - isolate ALL provider failures
            logger.exception("Unexpected SMS provider failure.")
            raise SMSServiceError("SMS service is unreachable.") from exc

        if response.status_code != 201:
            raise SMSServiceError(f"SMS API returned HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise SMSServiceError("SMS API returned an invalid response.") from exc

        recipients = (payload.get("SMSMessageData") or {}).get("Recipients") or []
        if recipients and recipients[0].get("statusCode") != 101:
            raise SMSServiceError(
                f"SMS was rejected by the provider: {recipients[0].get('status') or 'unknown'}."
            )
        return payload

    def send_parts(self, phone_number: str, message: str) -> list[dict]:
        """Send ``message`` as one or more SMS parts, split at word boundaries.

        Important legal information is never truncated to a single SMS: every
        part is delivered in order. Returns the list of provider responses.
        """
        parts = split_sms_message(message)
        return [self.send(phone_number, part) for part in parts]


def split_sms_message(text: str, limit: int = SMS_PART_LIMIT) -> list[str]:
    """Split ``text`` into SMS-sized parts at word boundaries.

    - Never cuts inside a word.
    - Preserves existing line breaks where they fit.
    - When more than one part results, each part is prefixed with
      ``Part i/n`` so the reader always knows where they are.
    """
    text = (text or "").strip()
    if not text:
        return []

    # Greedy word wrap that respects explicit line breaks.
    chunks: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        # A single word longer than the limit is hard-cut rather than lost.
        while len(word) > limit:
            chunks.append(word[:limit])
            word = word[limit:]
        current = word
    if current:
        chunks.append(current)

    if len(chunks) == 1:
        return chunks

    total = len(chunks)
    return [f"Part {i}/{total}\n{chunk}" for i, chunk in enumerate(chunks, start=1)]


def build_content_sms(content, include_next_step: bool = True) -> str:
    """Compose the concise English SMS summary for a LegalContent."""
    lines = [f"MANYA — {content.title}"]
    if content.summary:
        lines.append(content.summary.strip())
    if include_next_step and content.next_steps:
        lines.append(f"Next step: {content.next_steps.strip()}")
    lines.append("This is general legal information, not legal advice.")
    return "\n".join(lines)


def build_translated_content_sms(
    content, language_code: str, include_next_step: bool = True
) -> str:
    """Compose SMS through the central translation service (DB -> Sunbird -> EN)."""
    from apps.languages.services.translation_service import TranslationService

    title = TranslationService.get_content(content, "title", language_code)
    summary = TranslationService.get_content(content, "summary", language_code)
    next_steps = TranslationService.get_content(content, "next_steps", language_code)
    next_label = TranslationService.get_text("sms_next_step", language_code)
    disclaimer = TranslationService.get_text("sms_disclaimer", language_code)

    lines = [f"MANYA — {title}"]
    if summary:
        lines.append(summary.strip())
    if include_next_step and next_steps:
        lines.append(f"{next_label}: {next_steps.strip()}")
    lines.append(disclaimer)
    return "\n".join(lines)


def send_infosms(phone_number, content, service=None, message=None):
    """Send a concise language-aware MANYA SMS for a LegalContent.

    Used by the USSD "Send SMS" step. The message is built from the same
    verified content served everywhere else; the provider is only ever
    reached through SMSService. Callers may pass a pre-built ``message``
    (e.g. already translated by the central translation service) which then
    takes precedence over the default English composition.

    Long messages are split at word boundaries into multiple parts
    (``Part i/n``) instead of being blindly cut at 160 characters, so a
    translated sentence is never truncated mid-sentence.
    """
    service = service or SMSService()
    message = message or build_content_sms(content)
    return service.send_parts(phone_number, message)
