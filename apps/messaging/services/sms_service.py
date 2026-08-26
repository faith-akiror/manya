"""Two-way SMS conversation service.

Reuses the SAME verified legal database, translation layer and journey state
machine as USSD: an incoming SMS is routed through ``UssdService`` using a
stable per-phone session (``sms:<normalized phone>``), so a person texting
MANYA gets exactly the menus, legal content, referrals, policies, errors and
language persistence that USSD users get - translated end to end.

Provider specifics stay inside ``africastalking_sms.py``; this module never
talks to Africa's Talking HTTP APIs directly.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from apps.languages.models import Language
from apps.messaging.models import UserPreference
from apps.messaging.services.africastalking_sms import SMSService, split_sms_message
from apps.ussd.models import UssdSession
from apps.ussd.services.ussd_service import UssdService

logger = logging.getLogger(__name__)

SMS_SESSION_PREFIX = "sms:"
# After this much inactivity a conversation returns to the main menu, but the
# user's selected language is preserved - nobody should have to re-learn how
# to say their language just because they texted again a week later.
SESSION_TIMEOUT_HOURS = 24


def sms_session_id_for_phone(phone: str) -> str:
    """Stable session id for a phone number (fits UssdSession.session_id)."""
    return f"{SMS_SESSION_PREFIX}{phone}"[:64]


def normalize_sms_phone(raw: str) -> str:
    """Best-effort E.164-style normalisation for provider-supplied numbers."""
    phone = (raw or "").strip().replace(" ", "")
    if phone and not phone.startswith("+") and phone.isdigit():
        phone = f"+{phone}"
    return phone


def strip_ussd_prefix(response: str) -> str:
    """Turn a ``CON ...`` / ``END ...`` USSD frame into plain SMS text."""
    if response.startswith(("CON ", "END ")):
        return response[4:]
    return response


class SmsConversationService:
    """Drive the shared MANYA journey over two-way SMS."""

    def __init__(self, ussd_service=None, sms_service=None):
        self.ussd = ussd_service or UssdService()
        self.sms = sms_service or SMSService()

    # ------------------------------------------------------------------
    def process_incoming(self, phone: str, text: str) -> dict:
        """Handle one inbound SMS and reply (possibly multi-part).

        Never raises: any failure to *reply* is logged and reported in the
        result so the webhook can still acknowledge the provider with 200.
        """
        session = self._ensure_session(phone)
        self._expire_if_stale(session)

        result = self.ussd.handle(
            {
                "sessionId": session.session_id,
                "phoneNumber": phone,
                "text": (text or "").strip(),
            }
        )
        session.refresh_from_db()
        self._remember_language_preference(phone, session.language_code)

        reply = strip_ussd_prefix(result.get("response", ""))
        sent_parts = self._send_reply(phone, reply)
        return {
            "reply": reply,
            "parts_sent": sent_parts,
            "language_code": session.language_code,
        }

    # ------------------------------------------------------------------
    def _ensure_session(self, phone: str) -> UssdSession:
        session, _ = UssdSession.objects.get_or_create(
            session_id=sms_session_id_for_phone(phone),
            defaults={
                "phone_number": phone,
                "menu": "start",
                "channel": "sms",
            },
        )
        return session

    @staticmethod
    def _expire_if_stale(session: UssdSession) -> None:
        stale_after = timezone.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)
        if session.updated_at and session.updated_at < stale_after:
            session.menu = "main"
            session.data = {}
            session.save(update_fields=["menu", "data", "updated_at"])

    @staticmethod
    def _remember_language_preference(phone: str, language_code: str) -> None:
        """Mirror the chosen language into UserPreference (best effort)."""
        language = Language.objects.filter(code=language_code, is_active=True).first()
        try:
            UserPreference.objects.update_or_create(
                phone_number=phone,
                defaults={"preferred_language": language},
            )
        except Exception:  # noqa: BLE001 - preference sync must never break SMS
            logger.warning("Could not store language preference for %s", phone)

    def _send_reply(self, phone: str, reply: str) -> list[str]:
        """Split and send the reply; failures are logged, never raised."""
        try:
            parts = split_sms_message(reply)
            for part in parts:
                self.sms.send(phone, part)
            return parts
        except Exception as exc:  # noqa: BLE001 - isolate all provider failures
            logger.warning("Could not send SMS reply to %s: %s", phone, exc)
            return []
