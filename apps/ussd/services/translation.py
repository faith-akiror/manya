"""USSD translation helpers (single path through the central service)."""

from apps.languages.services.translation_service import TranslationService


def ui(session, key):
    """Translate an interface message for the session language."""
    return TranslationService.get_text(key, session.language_code)


def content(session, obj, field):
    """Translate database content for the current session language."""
    return TranslationService.get_content(obj, field, session.language_code)
