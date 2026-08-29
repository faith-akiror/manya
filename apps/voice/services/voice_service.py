"""Voice IVR state machine for MANYA.

Voice drives the SAME verified legal database, translation layer and session
state machine as USSD and SMS (``UssdService``), rendered as Africa's Talking
Voice XML. Content is localised through the same Sunbird-powered
``TranslationService`` every other channel uses.

Africa's Talking sends one notification per key press: the current
``sessionId`` and the pressed key in ``dtmfDigits``. We keep one
``UssdSession`` per Africa's Talking session (``channel="voice"``) so the
selected language, menu and navigation survive across key presses, exactly
like a USSD menu.
"""

import logging
import re

from apps.languages.models import Language
from apps.languages.services.translation_service import TranslationService
from apps.messaging.models import UserPreference
from apps.ussd.models import UssdSession
from apps.ussd.services.ussd_service import UssdService
from apps.voice.services.africastalking_voice import VoiceService

logger = logging.getLogger(__name__)

VOICE_SESSION_PREFIX = "voice:"
MENU_ITEM_RE = re.compile(r"^\d+\.\s")


def _normalize_digits(raw) -> str:
    """A key press is a single digit; keep the last one if several arrive."""
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    return digits[-1] if len(digits) > 1 else digits


def voice_session_id(at_session_id: str) -> str:
    """Namespaced id so voice conversations never collide with USSD/SMS."""
    return f"{VOICE_SESSION_PREFIX}{at_session_id}"[:64]


def _looks_like_menu(body: str) -> bool:
    """True when the spoken text is a numbered menu (two or more items)."""
    return sum(1 for line in str(body).splitlines() if MENU_ITEM_RE.match(line)) >= 2


def _strip_frame(response_text: str) -> str:
    """Remove the ``CON `` / ``END `` frame UssdService returns."""
    text = str(response_text or "")
    for prefix in ("CON ", "END "):
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text


class VoiceConversationService:
    """Resolve one voice notification into Africa's Talking Voice XML."""

    def __init__(self, ussd_service=None, voice_service=None):
        self.ussd = ussd_service or UssdService()
        self.voice = voice_service or VoiceService()

    def dispatch(self, payload, callback_url="") -> dict:
        """Handle one voice callback; returns ``{"xml": ..., "continue_flow": ...}``.

        Never raises for provider/DB failures: the caller must always receive a
        valid, friendly response so the call can end cleanly.
        """
        # Final notification: carries cost/duration details and must not be
        # processed as another IVR step.
        if str(payload.get("isActive") or "1") == "0":
            return self._result(self.voice.end_response(), continue_flow=False)

        session_id = str(payload.get("sessionId") or "").strip()
        caller = str(payload.get("callerNumber") or "").strip()
        if not session_id:
            return self._end_friendly()
        digits = _normalize_digits(payload.get("dtmfDigits"))

        session, created = UssdSession.objects.get_or_create(
            session_id=voice_session_id(session_id),
            defaults={"phone_number": caller, "menu": "start", "channel": "voice"},
        )
        if caller and (created or session.phone_number != caller):
            session.phone_number = caller
            session.save(update_fields=["phone_number"])

        result = self.ussd.handle(
            {
                "sessionId": session.session_id,
                "phoneNumber": caller or session.phone_number,
                "text": digits,
            }
        )
        session = result.get("session")
        if session is None:
            return self._end_friendly()
        session.refresh_from_db()
        self._remember_language_preference(caller, session.language_code)

        response_text = str(result.get("response") or "")
        continue_flow = response_text.startswith("CON ")
        body = _strip_frame(response_text)
        if not body:
            return self._end_friendly()

        language_code = session.language_code or "en"
        if continue_flow:
            key = (
                "voice_menu_prompt" if _looks_like_menu(body) else "voice_repeat_prompt"
            )
            prompt = TranslationService.get_text(key, language_code)
            xml = self.voice.continue_response(body, prompt, callback_url=callback_url)
        else:
            xml = self.voice.end_response(body)
        return self._result(xml, continue_flow=continue_flow)

    # ------------------------------------------------------------------
    def _result(self, xml, continue_flow=True):
        return {"xml": xml, "continue_flow": continue_flow}

    def _end_friendly(self):
        text = TranslationService.get_text("system_error", "en")
        return self._result(self.voice.end_response(text), continue_flow=False)

    @staticmethod
    def _remember_language_preference(phone, language_code):
        """Mirror the chosen language into UserPreference (best effort)."""
        if not phone:
            return
        try:
            language = Language.objects.filter(
                code=language_code, is_active=True
            ).first()
            UserPreference.objects.update_or_create(
                phone_number=phone,
                defaults={"preferred_language": language},
            )
        except Exception:  # noqa: BLE001 - preferences must never break a call
            logger.warning("Could not store voice language preference for %s", phone)
