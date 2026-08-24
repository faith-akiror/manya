"""Sunbird AI translation service (Sunflower model).

Sunbird AI (https://api.sunbird.ai) is MANYA's machine-translation layer.

IMPORTANT LEGAL PRINCIPLE:
Sunbird is the *translation* layer only. It is NEVER the source of legal
truth. Translations produced here are always saved as DRAFT legal content and
must be reviewed and verified by a human administrator before they become
public.

Endpoint (verified against the Sunbird OpenAPI spec):
    POST {base}/tasks/translate
    Body: {"text": ..., "target_language": "<iso>", "source_language": "<iso>"?}
    Auth: Authorization: Bearer <token>

The token is obtained from SUNBIRD /auth/token and provided via the
SUNBIRD_API_TOKEN environment variable. Never commit credentials.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# Languages Sunbird/Sunflower supports for translation (from its public
# OpenAPI documentation). Used when the API cannot be reached for a list.
SUNBIRD_SUPPORTED_CODES = [
    "ach",
    "eng",
    "lug",
    "teo",
    "lugbara",
    "lgg",
    "nyn",
    "sw",
    "xog",
    "luo",
    "myx",
    "cgg",
    "ttj",
    "lth",
    "swa",
]


class SunbirdConfigurationError(Exception):
    """Sunbird credentials are missing."""


class SunbirdTranslationError(Exception):
    """Sunbird could not translate (network, timeout or API error)."""


class SunbirdTranslationService:
    """Thin, fault-tolerant client for the Sunbird AI translation API."""

    def __init__(self, token=None, base_url=None, timeout=60):
        self.token = token if token is not None else os.getenv("SUNBIRD_API_TOKEN", "")
        self.base_url = (
            base_url or os.getenv("SUNBIRD_BASE_URL", "https://api.sunbird.ai")
        ).rstrip("/")
        self.timeout = timeout
        self.http = requests.Session()
        if self.token:
            self.http.headers.update({"Authorization": f"Bearer {self.token}"})

    def is_configured(self) -> bool:
        """Return True when Sunbird AI credentials are configured."""
        return bool(self.token)

    def translate(self, text, target_language, source_language=None):
        """Translate ``text`` into ``target_language``. Returns the translation."""
        text = (text or "").strip()
        if not text:
            return ""
        if not self.token:
            raise SunbirdConfigurationError("SUNBIRD_API_TOKEN is not configured.")

        payload = {"text": text, "target_language": target_language}
        if source_language:
            payload["source_language"] = source_language

        try:
            response = self.http.post(
                f"{self.base_url}/tasks/translate", json=payload, timeout=self.timeout
            )
        except requests.exceptions.Timeout as exc:
            raise SunbirdTranslationError("Sunbird request timed out.") from exc
        except requests.exceptions.RequestException as exc:
            raise SunbirdTranslationError("Sunbird is unreachable.") from exc

        if response.status_code not in (200, 201):
            raise SunbirdTranslationError(
                f"Sunbird returned HTTP {response.status_code}."
            )
        data = self._parse_json(response)
        translation = self._extract_translation(data)
        if not translation:
            raise SunbirdTranslationError("Sunbird returned an empty translation.")
        return translation

    def translate_content(self, content, target_language):
        """Translate the translatable fields of a LegalContent into a language.

        Returns a flat dict of ``field_name -> translated text``. It never
        writes to the database and never marks anything verified.
        """
        source_code = content.language.code if content.language else "en"
        translated = {}
        for field in (
            "title",
            "summary",
            "rights_information",
            "what_this_means",
            "next_steps",
            "documents_required",
        ):
            value = getattr(content, field, "")
            if not value:
                continue
            translated[field] = self.translate(
                value, target_language=target_language, source_language=source_code
            )
        return translated

    def get_supported_languages(self):
        """Return ISO codes Sunbird can translate into.

        Tries the API; falls back to the known supported set so callers can
        still render a language picker when the API is unreachable.
        """
        try:
            response = self.http.get(
                f"{self.base_url}/tasks/languages", timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                items = (
                    data
                    if isinstance(data, list)
                    else (data.get("languages") or data.get("data") or [])
                )
                codes = []
                for item in items:
                    if isinstance(item, str):
                        codes.append(item)
                    elif isinstance(item, dict):
                        raw = item.get("code") or item.get("iso_code") or item.get("id")
                        if raw:
                            codes.append(str(raw))
                if codes:
                    return codes
        except Exception as exc:  # noqa: BLE001 - never break the flow
            logger.warning("Sunbird language discovery failed: %s", exc)
        return sorted(SUNBIRD_SUPPORTED_CODES)

    # ------------------------------------------------------------------
    # helpers
    @staticmethod
    def _parse_json(response):
        try:
            data = response.json()
        except ValueError as exc:
            raise SunbirdTranslationError(
                "Sunbird returned an invalid response."
            ) from exc
        if not isinstance(data, dict):
            raise SunbirdTranslationError("Sunbird returned an invalid response.")
        return data

    @classmethod
    def _extract_translation(cls, data):
        """Tolerate the different JSON shapes returned by Sunbird."""
        for key in (
            "translation",
            "translated_text",
            "translatedText",
            "result",
            "text",
        ):
            value = data.get(key)
            if value:
                return str(value)
        nested = data.get("data")
        if isinstance(nested, dict):
            for key in (
                "translation",
                "translated_text",
                "translatedText",
                "result",
                "text",
            ):
                value = nested.get(key)
                if value:
                    return str(value)
        return ""
