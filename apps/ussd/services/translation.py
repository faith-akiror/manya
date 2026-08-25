"""USSD translation helpers."""

from apps.languages.services.content_translation import translated
from apps.languages.services.ui_translations import UITranslationService


def ui(session, key):
    """Translate an interface message."""
    return UITranslationService.get(key, session.language_code)


def content(session, obj, field):
    """Translate database content for the current session language."""
    return translated(obj, field, session.language_code)
