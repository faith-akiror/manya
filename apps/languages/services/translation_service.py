"""Central translation service for MANYA.

Every translation request flows through here:

    requested language
        -> ContentTranslation / UIMessage / Translation cache (database)
        -> Sunbird (only when the database has no translation)
        -> save to database
        -> return

Sunbird is therefore called at most once per missing translation and every
subsequent request hits the database. The service is language-agnostic: a new
language added in Django admin is picked up automatically with no code change.

All user-facing channels (USSD, REST API, SMS) must use this service so there
is a single code path that decides database -> Sunbird -> English fallback.
"""

import hashlib
import logging

from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType

from apps.languages.models import (
    ContentTranslation,
    Language,
    Translation,
    UIMessage,
)
from apps.languages.services.content_translation import ContentTranslationService
from apps.languages.services.sunbird_translation import get_provider
from apps.languages.services.ui_translations import DEFAULT_ENGLISH, UITranslationService

logger = logging.getLogger(__name__)

# (model label, model name, translatable fields) — the canonical list of what
# dynamic content MANYA can translate. Fields are resolved defensively.
TRANSLATABLE_MODELS = {
    "LegalCategory": {"app": "legal", "fields": ("name", "description")},
    "LegalTopic": {"app": "legal", "fields": ("name", "description")},
    "LegalContent": {
        "app": "legal",
        "fields": (
            "title",
            "summary",
            "rights_information",
            "what_this_means",
            "next_steps",
            "documents_required",
        ),
    },
    "PolicyUpdate": {"app": "policies", "fields": ("title", "summary")},
    "Referral": {"app": "referrals", "fields": ("name", "description", "location")},
}


def _text_hash(text: str) -> str:
    return hashlib.sha256((text or "").strip().encode("utf-8")).hexdigest()


def request_language(code):
    """Resolve an active ``Language``; falls back to the default language."""
    if code:
        lang = Language.objects.filter(code=code, is_active=True).first()
        if lang:
            return lang
    return Language.get_default()


class TranslationService:
    """Resolve translations with database-first, Sunbird-on-miss semantics."""

    DEFAULT_SOURCE = "en"

    # ------------------------------------------------------------------
    # Free-text translation cache (Translation model) -> Sunbird -> fallback
    @classmethod
    def translate(
        cls,
        text,
        target_language,
        source_language="en",
        content_type=None,
        content_id=None,
    ):
        """Translate free text, caching the result in ``Translation``.

        Returns the best-effort translation (or the original text) and never
        raises, so it is safe to call inside a USSD/API request while Sunbird
        is down.
        """
        text = (text or "").strip()
        if not text:
            return ""
        if target_language == source_language:
            return text

        cache_key = _text_hash(text)
        cached = Translation.objects.filter(
            source_hash=cache_key,
            source_language=source_language,
            target_language=target_language,
        ).first()
        if cached and cached.translated_text:
            return cached.translated_text

        provider = get_provider()
        translation = provider.translate(text, source_language, target_language)
        if not translation:
            logger.warning(
                "No translation available (%s -> %s); using source text.",
                source_language,
                target_language,
            )
            return text

        defaults = {
            "source_text": text,
            "translated_text": translation,
        }
        if content_type is not None:
            defaults["content_type"] = str(content_type)[:100]
        if content_id is not None:
            defaults["content_id"] = str(content_id)[:100]
        Translation.objects.update_or_create(
            source_hash=cache_key,
            source_language=source_language,
            target_language=target_language,
            defaults=defaults,
        )
        return translation

    @classmethod
    def translate_object(cls, obj, fields, target_language):
        """Translate several object fields at once; returns ``{field: text}``.

        Uses the same database-first / Sunbird-on-miss path as USSD, so results
        are cached in ContentTranslation and reused across channels.
        """
        return {
            field: cls.get_content(obj, field, target_language)
            for field in fields
            if getattr(obj, field, "")
        }

    # ------------------------------------------------------------------
    # UI messages (UIMessage) -> Sunbird -> English fallback
    @classmethod
    def get_text(cls, key, language, auto_translation=True):
        """Return interface text for ``key`` in ``language`` (USSD etc.)."""
        lang = request_language(language)
        if lang is None:
            return UITranslationService.get(key, "en")
        code = lang.code

        # 1. Requested language already has the message.
        row = UIMessage.objects.filter(language=lang, key=key).first()
        if row and row.text:
            return row.text

        # 2. English source.
        en_row = UIMessage.objects.filter(language__code="en", key=key).first()
        source_text = ""
        if en_row and en_row.text:
            source_text = en_row.text
        if not source_text:
            source_text = DEFAULT_ENGLISH.get(key, "")
        if not source_text:
            return UITranslationService.get(key, code)

        # 3. English requested -> return source directly.
        if code == "en":
            return source_text

        # 4. Auto-translate (only when enabled and supported) and persist.
        if auto_translation:
            provider = get_provider()
            if provider.is_configured() and provider.is_supported(code):
                translated = provider.translate(source_text, "en", code)
                if translated:
                    UIMessage.objects.update_or_create(
                        language=lang,
                        key=key,
                        defaults={"text": translated},
                    )
                    return translated

        # 5. Safe English fallback.
        return source_text
# ------------------------------------------------------------------
    # Dynamic object content (ContentTranslation) -> Sunbird -> English fallback
    @classmethod
    def get_content(cls, obj, field, language_code, fallback=True, auto_translation=True):
        """Return a translated object field for a language.

        Checks ContentTranslation first, generates + persists via Sunbird when
        missing, and finally falls back to the original (English) value.
        """
        if obj is None:
            return ""
        original = getattr(obj, field, "") or ""
        lang = request_language(language_code)
        if lang is None:
            return original

        source_lang = cls._source_language(obj)
        # English (source) is never "translated".
        if lang.code == source_lang or lang.code == "en":
            return original

        # Existing usable translation (verified or Sunbird-generated).
        existing = ContentTranslationService.get(
            obj, field, lang.code, fallback=False
        )
        if existing:
            return existing

        if not auto_translation or not original:
            return original if fallback else ""

        provider = get_provider()
        if not (provider.is_configured() and provider.is_supported(lang.code)):
            return original if fallback else ""

        translated = provider.translate(original, source_lang, lang.code)
        if not translated:
            logger.warning(
                "Translation failed for %s.%s field=%s lang=%s",
                obj._meta.app_label,
                obj._meta.model_name,
                field,
                lang.code,
            )
            return original if fallback else ""

        cls._persist_content_translation(
            obj, field, lang, translated, source="sunbird", status="machine_translated"
        )
        return translated

    @staticmethod
    def _source_language(obj):
        for name in ("language", "languages"):
            value = getattr(obj, name, None)
            code = getattr(value, "code", None)
            if code:
                return code
        return TranslationService.DEFAULT_SOURCE

    @staticmethod
    def _persist_content_translation(obj, field, language, text, source, status):
        """Never overwrite a reviewed/manual translation (checked by caller)."""
        ContentTranslation.objects.update_or_create(
            language=language,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            field=field,
            defaults={
                "text": text,
                "is_verified": False,
                "translation_source": source,
                "translation_status": status,
            },
        )

    # ------------------------------------------------------------------
    # Bulk generation (management command / admin)
    @classmethod
    def generate_missing_for_language(cls, language_code, include_ui=False):
        """Generate translations for all translatable models into a language.

        Returns a dict with ``created``/``skipped``/``failed`` counts. Does not
        raise; individual errors are logged and counted.
        """
        lang = Language.objects.filter(code=language_code, is_active=True).first()
        if lang is None:
            return {"created": 0, "skipped": 0, "failed": 0}

        created_count = skipped = failed = 0
        for model_name, spec in TRANSLATABLE_MODELS.items():
            model = django_apps.get_model(spec["app"], model_name)
            for obj in model.objects.all():
                content_type = ContentType.objects.get_for_model(obj)
                for field in spec["fields"]:
                    if not hasattr(obj, field):
                        continue
                    try:
                        exists = ContentTranslation.objects.filter(
                            language=lang,
                            content_type=content_type,
                            object_id=obj.pk,
                            field=field,
                        ).exists()
                        if exists:
                            skipped += 1
                            continue
                        cls.get_content(obj, field, lang.code)
                        saved = ContentTranslation.objects.filter(
                            language=lang,
                            content_type=content_type,
                            object_id=obj.pk,
                            field=field,
                        ).exists()
                        if saved:
                            created_count += 1
                        else:
                            skipped += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("generate_missing failed: %s", exc)
                        failed += 1

        if include_ui:
            for key in set(DEFAULT_ENGLISH) | {
                r.key for r in UIMessage.objects.filter(language__code="en")
            }:
                try:
                    before = UIMessage.objects.filter(language=lang, key=key).exists()
                    cls.get_text(key, lang.code)
                    after = UIMessage.objects.filter(language=lang, key=key).exists()
                    if after and not before:
                        created_count += 1
                    else:
                        skipped += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning("generate_missing (ui) failed: %s", exc)
                    failed += 1

        return {"created": created_count, "skipped": skipped, "failed": failed}