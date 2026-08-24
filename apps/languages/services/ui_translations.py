"""Database-backed interface (UI) translations.

All interface strings shown by MANYA (website menus, USSD menus, buttons) are
looked up from the ``UIMessage`` table keyed by language + key. When a language
has no entry for a key the English fallback is used, so a new language can be
added with only a few translated strings.

Admins can add/override any key in Django admin without touching code.
"""

from django.core.cache import cache

from apps.languages.models import Language, UIMessage

DEFAULT_ENGLISH = {
    "home": "Home",
    "legal_information": "Legal Information",
    "find_help": "Find Help",
    "policy_updates": "Policy Updates",
    "about": "About MANYA",
    "change_language": "Change Language",
    "search": "Search",
    "next": "Next",
    "back": "Back",
    "continue": "Continue",
    "menu": "Menu",
    "welcome": "Welcome to MANYA",
    "tagline": "Know your rights. Know your next step.",
    "invalid_choice": "Invalid choice. Please try again.",
    "missing_translation_message": "This information is not yet available in your selected language.",
    "view_in_english": "View in English",
    "change_language_prompt": "Choose your language",
    "no_verified_info": (
        "We couldn't find verified information on this issue. Please consult a "
        "qualified legal professional or a verified legal-aid service."
    ),
    "choose": "Choose",
    "send_sms": "Send SMS",
    "what_should_i_do": "What should I do?",
    "understand_my_rights": "Understand my rights",
    "documents_i_need": "Documents I need",
    "listen": "Listen",
    "i_have_a_problem": "I have a problem",
    "know_my_rights": "Know my rights",
    "find_legal_help": "Find legal help",
    "choose_issue": "Choose your issue",
    "sms_sent": "We have sent the information to your phone by SMS.",
    "sms_failed": "We could not send the SMS right now. Please try again later.",
    "exit": "Thank you for using MANYA.",
}


class UITranslationService:
    """Resolve interface strings for a language code."""

    cache_timeout = 300

    @classmethod
    def get(
        cls, key: str, language_code: str = "en", default: str | None = None
    ) -> str:
        english_default = DEFAULT_ENGLISH.get(key)
        if language_code == "en":
            return english_default if english_default is not None else (default or key)
        try:
            lang = Language.objects.filter(code=language_code).first()
            if lang:
                entry = UIMessage.objects.filter(language=lang, key=key).first()
                if entry and entry.text:
                    return entry.text
        except Exception:
            pass
        return english_default if english_default is not None else (default or key)

    @classmethod
    def bundle(cls, language_code: str) -> dict[str, str]:
        """All UI strings for a language merged over English defaults."""
        cache_key = f"ui:{language_code}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        bundle = dict(DEFAULT_ENGLISH)
        language = Language.objects.filter(code=language_code).first()
        if language and language_code != "en":
            for row in UIMessage.objects.filter(language=language):
                bundle[row.key] = row.text
        cache.set(cache_key, bundle, cls.timeout)
        return bundle
