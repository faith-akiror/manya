"""Translation workflow (Sunbird + human review).

Flow:
    Admin open verified English content
    -> select language(s) to translate into
    -> Sunbird AI generates a translation
    -> MANYA saves it as DRAFT (NEVER auto-verified)
    -> a human reviews and marks it VERIFIED in Django admin
    -> then it becomes public on the website / USSD / SMS.

Existing verified translations are preserved and continue to work even when
Sunbird is unavailable — we only call Sunbird when explicitly (re)translating.
"""

import logging

from apps.languages.models import Language
from apps.languages.services.sunbird import (
    SunbirdTranslationService,
)
from apps.legal.models import LegalContent

logger = logging.getLogger(__name__)

TRANSLATABLE_FIELDS = (
    "title",
    "summary",
    "rights_information",
    "what_this_means",
    "next_steps",
    "documents_required",
)


class TranslationWorkflow:
    """Generate and store AI translations as human-reviewable drafts."""

    def __init__(self, sunbird=None):
        self.sunbird = sunbird or SunbirdTranslationService()

    def generate_translation(
        self, content: LegalContent, target_language: Language, force: bool = False
    ) -> LegalContent:
        """Translate ``content`` into ``target_language``.

        Creates (or updates) a DRAFT record. Raises Sunbird* errors on failure;
        never marks the result VERIFIED.
        """
        if target_language.code == content.language.code:
            raise ValueError("A record cannot be translated into its own language.")

        existing = (
            LegalContent.objects.filter(topic=content.topic, language=target_language)
            .exclude(verification_status="ARCHIVED")
            .first()
        )
        if existing and existing.verification_status == "VERIFIED" and not force:
            raise ValueError(
                "A verified translation already exists for this language. Delete it "
                "or use force=True to retranslate."
            )

        translated_fields = self.sunbird.translate_content(
            content, target_language=target_language.code
        )
        if not translated_fields:
            raise ValueError("Sunbird returned no translated fields.")

        # Start from the source content's translatable fields so nothing is
        # lost, then override only the fields Sunbird actually translated.
        defaults = {
            "original_content": content,
            "source": content.source,
            "source_title": content.source_title,
            "source_url": content.source_url,
            "legal_reference": content.legal_reference,
            "section_reference": content.section_reference,
            "disclaimer": content.disclaimer,
            "verification_status": "DRAFT",
            "last_verified": None,
        }
        for field in TRANSLATABLE_FIELDS:
            defaults[field] = getattr(content, field, "")
        for field in TRANSLATABLE_FIELDS:
            if field in translated_fields and translated_fields[field]:
                defaults[field] = translated_fields[field]

        if existing:
            for field, value in defaults.items():
                setattr(existing, field, value)
            existing.save()
            return existing

        return LegalContent.objects.create(
            topic=content.topic,
            language=target_language,
            **defaults,
        )

    def generate_translations(
        self,
        content: LegalContent,
        languages,
        force: bool = False,
    ) -> list[LegalContent]:
        """Translate ``content`` into an iterable of Language instances.

        A single failed API call raises SunbirdTranslationError; callers choose
        whether to abort or continue. Nothing is automatically published.
        """
        created = []
        for language in languages:
            created.append(self.generate_translation(content, language, force=force))
        return created

    @staticmethod
    def get_supported_languages(content: LegalContent):
        """Languages that it makes sense to translate this content into."""
        used = set(
            LegalContent.objects.filter(topic=content.topic)
            .exclude(verification_status="ARCHIVED")
            .values_list("language__code", flat=True)
        )
        used.add(content.language.code)
        return Language.active_public().exclude(code__in=used)
