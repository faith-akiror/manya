"""Assemble the public dashboard from live database records.

Counts and badges are derived from existing models only. Empty sections stay
empty — this module never invents usage numbers or verification status.
"""

from collections import Counter, defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, Q

from apps.languages.models import ContentTranslation, Language
from apps.legal.models import LegalCategory, LegalContent, LegalSource, LegalTopic
from apps.legal.services.content_query import (
    any_verified_content,
    available_languages_for_topic,
    get_verified_content,
)
from apps.messaging.models import IncomingSMS
from apps.messaging.services.sms_service import sms_session_id_for_phone
from apps.ussd.models import UssdSession

UNVERIFIED_STATUSES = ("DRAFT", "REVIEW")


def _language_chip(language):
    return {
        "code": language.code,
        "label": language.native_name or language.name or language.code,
    }


def build_dashboard():
    """Return the template context for GET /dashboard/."""
    languages = list(Language.active_public())
    language_by_code = {lang.code: lang for lang in Language.objects.all()}

    return {
        "languages": languages,
        "categories": _legal_catalogue(language_by_code),
        "demand": _community_questions(),
        "sources": _active_sources(),
    }


def _legal_catalogue(language_by_code):
    """Categories and topics with verified vs draft language coverage.

    A topic is verified only when ``get_verified_content`` would return a
    row: at least one ``LegalContent`` record with status ``VERIFIED``.
    """
    categories = (
        LegalCategory.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "topics",
                queryset=LegalTopic.objects.filter(is_active=True).order_by(
                    "display_order", "name"
                ),
            )
        )
        .order_by("display_order", "name")
    )
    topics = [
        topic
        for category in categories
        for topic in category.topics.all()
    ]
    draft_languages_by_topic = _draft_languages_by_topic(topics)

    catalogue = []
    for category in categories:
        catalogue.append(
            {
                "name": category.name,
                "slug": category.slug,
                "topics": [
                    _topic_row(topic, language_by_code, draft_languages_by_topic)
                    for topic in category.topics.all()
                ],
            }
        )
    return catalogue


def _topic_row(topic, language_by_code, draft_languages_by_topic):
    verified_codes = list(available_languages_for_topic(topic))
    verified_languages = [
        _language_chip(language_by_code[code])
        for code in verified_codes
        if code in language_by_code
    ]

    draft_codes = sorted(
        code
        for code in draft_languages_by_topic.get(topic.pk, set())
        if code not in verified_codes
    )
    draft_languages = [
        _language_chip(language_by_code[code])
        for code in draft_codes
        if code in language_by_code
    ]

    verified_record = get_verified_content(topic, "en") or any_verified_content(topic)
    title = verified_record.title if verified_record else topic.name

    if verified_codes:
        status = "verified"
    elif draft_codes:
        status = "draft"
    else:
        status = "empty"

    return {
        "title": title,
        "slug": topic.slug,
        "status": status,
        "verified_languages": verified_languages,
        "draft_languages": draft_languages,
    }


def _draft_languages_by_topic(topics):
    """Languages that have unpublished or Sunbird-only text for a topic."""
    if not topics:
        return {}

    topic_ids = [topic.pk for topic in topics]
    draft_by_topic = defaultdict(set)

    for content in LegalContent.objects.filter(
        topic_id__in=topic_ids, verification_status__in=UNVERIFIED_STATUSES
    ).select_related("language"):
        if content.language_id:
            draft_by_topic[content.topic_id].add(content.language.code)

    topic_ct = ContentType.objects.get_for_model(LegalTopic)
    content_ct = ContentType.objects.get_for_model(LegalContent)
    contents = list(
        LegalContent.objects.filter(topic_id__in=topic_ids).values("id", "topic_id")
    )
    content_to_topic = {row["id"]: row["topic_id"] for row in contents}
    content_ids = list(content_to_topic.keys())

    sunbird_filter = Q(content_type=topic_ct, object_id__in=topic_ids)
    if content_ids:
        sunbird_filter |= Q(content_type=content_ct, object_id__in=content_ids)

    for row in ContentTranslation.objects.filter(
        translation_source="sunbird"
    ).filter(sunbird_filter).select_related("language"):
        if row.content_type_id == topic_ct.id:
            topic_id = row.object_id
        else:
            topic_id = content_to_topic.get(row.object_id)
        if topic_id and row.language_id:
            draft_by_topic[topic_id].add(row.language.code)

    return draft_by_topic


def _community_questions():
    """Topic demand from stored USSD and SMS conversation selections.

    USSD stores the path on ``UssdSession.data["user_selection"]`` as
    ``[category_slug, topic_slug]``. Two-way SMS uses the same session model
    (``sms:<phone>``). Incoming SMS rows do not store a menu path; they are
    joined to that session so SMS conversations are included without
    fabricating counts.
    """
    topic_by_slug = {
        topic.slug: topic
        for topic in LegalTopic.objects.filter(
            is_active=True, category__is_active=True
        ).select_related("category")
    }

    counts = Counter()
    counted_sessions = set()

    def record_session(session):
        if session is None or session.session_id in counted_sessions:
            return
        counted_sessions.add(session.session_id)
        data = session.data if isinstance(session.data, dict) else {}
        selection = data.get("user_selection") or []
        if not isinstance(selection, list) or len(selection) < 2:
            return
        slug = selection[1]
        if slug in topic_by_slug:
            counts[slug] += 1

    sessions = list(UssdSession.objects.all())
    sessions_by_id = {session.session_id: session for session in sessions}
    sessions_by_phone = {}
    for session in sessions:
        if session.phone_number:
            sessions_by_phone.setdefault(session.phone_number, session)
        record_session(session)

    sms_count = IncomingSMS.objects.count()
    for phone in IncomingSMS.objects.values_list("phone_number", flat=True).distinct():
        session = sessions_by_id.get(sms_session_id_for_phone(phone))
        if session is None:
            session = sessions_by_phone.get(phone)
        record_session(session)

    max_count = max(counts.values()) if counts else 0
    bars = []
    for slug, count in counts.most_common():
        topic = topic_by_slug[slug]
        percent = round((count / max_count) * 100) if max_count else 0
        bars.append(
            {
                "title": topic.name,
                "category": topic.category.name,
                "count": count,
                "percent": percent,
            }
        )

    return {
        "bars": bars,
        "session_count": len(sessions),
        "sms_count": sms_count,
        "selection_count": sum(counts.values()),
    }


def _active_sources():
    sources = []
    for source in LegalSource.objects.filter(status="ACTIVE").order_by(
        "authority_level", "name"
    ):
        sources.append(
            {
                "name": source.name,
                "organization": source.organization,
                "authority_level": source.authority_level,
                "authority_label": source.get_authority_level_display(),
                "last_verified_at": source.last_verified_at,
                "next_review_date": source.next_review_date,
                "requires_review": source.requires_review,
            }
        )
    return sources
