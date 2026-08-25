"""Database-driven content translation service."""

from django.contrib.contenttypes.models import ContentType

from apps.languages.models import ContentTranslation, Language


class ContentTranslationService:
    """Resolve verified database translations."""

    @staticmethod
    def get(obj, field, language_code, fallback=True):
        """Return translated content.

        For non-English languages, a verified translation is required.

        If no translation exists and fallback=True, return the original
        database value. Set fallback=False to explicitly require a verified
        translation and avoid silently showing English legal content to users
        who selected another language.
        """

        if obj is None:
            return ""

        original = getattr(obj, field, "") or ""

        if not language_code:
            return original

        language = Language.objects.filter(code=language_code, is_active=True).first()
        if language is None:
            return original

        content_type = ContentType.objects.get_for_model(obj)

        translation = (
            ContentTranslation.objects.filter(
                language=language,
                content_type=content_type,
                object_id=obj.pk,
                field=field,
                is_verified=True,
            )
            .values_list("text", flat=True)
            .first()
        )

        if translation:
            return translation

        if fallback:
            return original

        return ""


def translated(obj, field, language_code):
    """Convenience wrapper."""
    return ContentTranslationService.get(obj=obj, field=field, language_code=language_code)
