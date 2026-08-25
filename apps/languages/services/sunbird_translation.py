"""Sunbird AI translation adapter — the single Sunbird entry point.

This module wraps ``apps.languages.services.sunbird.SunbirdTranslationService``
(aliased here as ``SunbirdHTTPClient``), which is the piece that actually makes
the HTTP request to ``POST {SUNBIRD_BASE_URL}/tasks/translate``.

Responsibilities of this adapter:

* read the ``SUNBIRD_*`` Django settings / environment variables,
* map MANYA language codes (database ``Language.code``, e.g. ``lg``) to the
  ISO-639 codes Sunbird uses (e.g. ``lug``),
* decide whether a target language is supported without assuming it,
* normalise every failure (timeout, HTTP error, malformed JSON, unsupported
  language) into a ``None`` return so the translation service can fall back to
  English instead of breaking USSD.

The adapter NEVER raises. It returns the translated string, or ``None`` when
Sunbird is disabled, mis-configured, unreachable, or does not support the
requested language.

Secrets (SUNBIRD_API_TOKEN / authorization headers) are never logged.
"""

import logging
import time

from django.conf import settings

from apps.languages.services.sunbird import SunbirdTranslationService as SunbirdHTTPClient

logger = logging.getLogger(__name__)

# MANYA database language codes -> Sunbird translation target codes.
# "en" maps to "eng" and "lg" maps to "lug"; the rest are already the
# three-letter codes Sunbird uses.
MANYA_TO_SUNBIRD = {
    "en": "eng",
    "lg": "lug",
    "teo": "teo",
    "ach": "ach",
    "sw": "swa",
    "swa": "swa",
    "luo": "luo",
    "nyn": "nyn",
    "xog": "xog",
    "cgg": "cgg",
    "lgg": "lgg",
    "ttj": "ttj",
    "lth": "lth",
    "myx": "myx",
    "lugbara": "lugbara",
}

SUNBIRD_TO_MANYA = {v: k for k, v in MANYA_TO_SUNBIRD.items()}

# Fallback when the Sunbird language-discovery endpoint cannot be reached.
# Kept in sync with apps.languages.services.sunbird.SUNBIRD_SUPPORTED_CODES.
_KNOWN_SUPPORTED = {
    "ach",
    "eng",
    "lug",
    "teo",
    "lugbara",
    "lgg",
    "nyn",
    "sw",
    "swa",
    "xog",
    "luo",
    "myx",
    "cgg",
    "ttj",
    "lth",
}


def to_sunbird_code(code):
    """Map a MANYA language code to the ISO code Sunbird expects."""
    if not code:
        return code
    return MANYA_TO_SUNBIRD.get(code) or code


def from_sunbird_code(code):
    """Map a Sunbird ISO code back to the MANYA database language code."""
    if not code:
        return code
    return SUNBIRD_TO_MANYA.get(code) or code


def get_provider():
    """Return a configured SunbirdTranslationService adapter.

    Tests patch ``SunbirdTranslationService.translate`` on this module to avoid
    any real HTTP traffic.
    """
    return SunbirdTranslationService(
        enabled=getattr(settings, "SUNBIRD_ENABLED", False),
        timeout=getattr(settings, "SUNBIRD_TIMEOUT", 10),
    )
class SunbirdTranslationService:
    """High-level, fault-tolerant Sunbird adapter (see module docstring).

    Decorates the real HTTP client in ``apps.languages.services.sunbird`` with
    MANYA code mapping, support checks and safe failure handling. This is the
    class USSD/API/management commands should use; never call the HTTP client
    directly from views/services/models.
    """

    _supported_at = 0.0
    _supported_codes = None

    def __init__(self, enabled=None, timeout=None):
        self.enabled = (
            enabled
            if enabled is not None
            else getattr(settings, "SUNBIRD_ENABLED", False)
        )
        self.timeout = timeout or getattr(settings, "SUNBIRD_TIMEOUT", 10)
        self._http = SunbirdHTTPClient(token=self.token, timeout=self.timeout)

    @property
    def token(self):
        return getattr(settings, "SUNBIRD_API_TOKEN", "") or ""

    @property
    def base_url(self):
        return getattr(settings, "SUNBIRD_BASE_URL", "https://api.sunbird.ai")

    def is_configured(self) -> bool:
        """True when Sunbird is enabled AND a token is present."""
        return self.enabled and bool(self.token)

    def is_supported(self, language_code: str, refresh: bool = False) -> bool:
        """Whether Sunbird can translate into ``language_code``.

        Checks the actual Sunbird language list when reachable; falls back to
        the known supported set so USSD never breaks on a network failure.
        """
        if not language_code:
            return False
        target = to_sunbird_code(language_code)
        known = target in _KNOWN_SUPPORTED
        cached_expired = (
            self._supported_codes is None
            or time.monotonic() - self._supported_at > 3600
        )
        if not refresh and known and not cached_expired:
            return True
        try:
            codes = self._http.get_supported_languages() or []
        except Exception as exc:  # noqa: BLE001 - discovery must never crash USSD
            logger.warning("Sunbird language discovery failed: %s", exc)
            codes = []
        if codes:
            SunbirdTranslationService._supported_codes = set(codes)
            SunbirdTranslationService._supported_at = time.monotonic()
        return target in (self._supported_codes or _KNOWN_SUPPORTED)

    def translate(self, text, source_language, target_language):
        """Translate ``text`` from ``source_language`` to ``target_language``.

        Returns the translated string, or ``None`` when Sunbird is disabled,
        has no token, does not support the target language, or the API call
        fails for any reason. Never raises.
        """
        text = (text or "").strip()
        if not text:
            return ""
        if source_language == target_language:
            return text
        if not self.is_configured():
            return None
        if not self.is_supported(target_language):
            logger.warning(
                "Sunbird does not support target language '%s'; falling back.",
                target_language,
            )
            return None

        payload_lang = to_sunbird_code(target_language)
        payload_source = to_sunbird_code(source_language) or "eng"
        try:
            translation = self._http.translate(
                text,
                target_language=payload_lang,
                source_language=payload_source,
            )
        except Exception as exc:  # noqa: BLE001 - Sunbird errors must not break USSD
            logger.warning(
                "Sunbird translation failed (%s -> %s): %s",
                source_language,
                target_language,
                exc,
            )
            return None
        if translation is None:
            return None
        return translation if (translation or "").strip() else None
