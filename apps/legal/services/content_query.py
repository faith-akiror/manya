"""Content query helpers used by the public API, USSD and SMS.

All channels must read the SAME verified legal database. Only ``VERIFIED``
content is ever returned publicly.
"""

from apps.legal.models import LegalContent


def get_verified_content(topic, language_code: str):
    """Return the VERIFIED content for a topic + language (or None)."""
    return (
        LegalContent.objects.filter(
            topic=topic,
            language__code=language_code,
            verification_status="VERIFIED",
        )
        .select_related("source", "language")
        .first()
    )


def available_languages_for_topic(topic):
    """ISO codes that have VERIFIED content for this topic."""
    return list(
        LegalContent.objects.filter(topic=topic, verification_status="VERIFIED")
        .values_list("language__code", flat=True)
        .distinct()
    )


def any_verified_content(topic):
    return (
        get_verified_content(topic, "en")
        or LegalContent.objects.filter(
            topic=topic, verification_status="VERIFIED"
        ).first()
    )
