"""Serializers for the legal app (public, verified data only)."""

from rest_framework import serializers

from apps.languages.services.content_translation import ContentTranslationService
from apps.languages.services.translation_service import TranslationService
from apps.legal.models import LegalCategory, LegalContent, LegalSource, LegalTopic
from apps.legal.services.content_query import (
    available_languages_for_topic,
    get_verified_content,
)

# Legal content fields that are sent through the central translation service
# when a non-English language is requested on the API.
LEGAL_CONTENT_TRANSLATABLE_FIELDS = (
    "title",
    "summary",
    "rights_information",
    "what_this_means",
    "next_steps",
    "documents_required",
)


class SourcePublicSerializer(serializers.ModelSerializer):
    status_message = serializers.CharField(
        source="status_display_message", read_only=True
    )

    class Meta:
        model = LegalSource
        fields = [
            "id",
            "name",
            "organization",
            "source_type",
            "url",
            "document_title",
            "document_identifier",
            "chapter",
            "publication_date",
            "effective_date",
            "version",
            "jurisdiction",
            "status",
            "status_message",
            "authority_level",
            "is_authoritative",
        ]


class LegalContentPublicSerializer(serializers.ModelSerializer):
    """Server only VERIFIED content through this serializer."""

    language_code = serializers.CharField(source="language.code", read_only=True)
    language_name = serializers.CharField(source="language.name", read_only=True)
    source = SourcePublicSerializer(read_only=True)

    class Meta:
        model = LegalContent
        fields = [
            "title",
            "summary",
            "rights_information",
            "what_this_means",
            "next_steps",
            "documents_required",
            "source_title",
            "source_url",
            "legal_reference",
            "section_reference",
            "last_verified",
            "disclaimer",
            "language_code",
            "language_name",
            "source",
        ]


class LegalCategorySerializer(serializers.ModelSerializer):
    """Category list payload.

    When ``?lang=<code>`` is supplied, stored translations are applied via a
    DATABASE-ONLY fast path: list views never trigger Sunbird fan-out, they
    simply fall back to English until a translation exists in the database.
    """

    topic_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = LegalCategory
        fields = ["id", "name", "slug", "description", "display_order", "topic_count"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self.context.get("language_code") or ""
        if lang and lang != "en":
            for field in ("name", "description"):
                if data.get(field):
                    data[field] = ContentTranslationService.get(instance, field, lang)
        return data


class LegalTopicBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalTopic
        fields = ["id", "name", "slug", "description", "display_order"]


class LegalCategoryDetailSerializer(serializers.ModelSerializer):
    """Category detail with its active topics and their language availability."""

    topics = serializers.SerializerMethodField()

    class Meta:
        model = LegalCategory
        fields = ["id", "name", "slug", "description", "topics"]

    def _lang(self):
        request = self.context.get("request")
        return self.context.get("language_code") or (
            request.query_params.get("lang", "en") if request else "en"
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = self._lang()
        if lang and lang != "en":
            for field in ("name", "description"):
                if data.get(field):
                    data[field] = TranslationService.get_content(instance, field, lang)
        return data

    def get_topics(self, category):
        topics = category.topics.filter(is_active=True)
        lang = self._lang()
        results = []
        for topic in topics:
            name = topic.name
            description = topic.description
            if lang != "en":
                # Full service path: stored translation -> Sunbird -> English.
                name = TranslationService.get_content(topic, "name", lang)
                if description:
                    description = TranslationService.get_content(
                        topic, "description", lang
                    )
            results.append(
                {
                    "name": name,
                    "slug": topic.slug,
                    "description": description,
                    "available_languages": available_languages_for_topic(topic),
                }
            )
        return results


class LegalTopicDetailSerializer(serializers.Serializer):
    """Topic with the requested-language content resolved from verified records."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()
    category = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    missing_translation = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()

    def get_category(self, topic):
        request = self.context["request"]
        lang_code = self.context.get("language_code") or (
            request.query_params.get("lang") or "en"
        )
        name = topic.category.name
        if lang_code and lang_code != "en":
            # Same central service USSD/SMS use: DB -> Sunbird -> English.
            name = TranslationService.get_content(topic.category, "name", lang_code)
        return {
            "name": name,
            "slug": topic.category.slug,
        }

    def get_content(self, topic):
        request = self.context["request"]
        lang_code = self.context.get("language_code") or (
            request.query_params.get("lang") or "en"
        )
        content = get_verified_content(topic, lang_code)
        if content is None and lang_code != "en":
            content = get_verified_content(topic, "en")
        if content is None:
            return None
        data = LegalContentPublicSerializer(content, context=self.context).data
        # If the requested language is not English but only the English record
        # exists, resolve every translatable field through the SAME translation
        # service used by USSD (database -> Sunbird -> English fallback).
        if content.language.code == "en" and lang_code and lang_code != "en":
            for field in LEGAL_CONTENT_TRANSLATABLE_FIELDS:
                if data.get(field):
                    data[field] = TranslationService.get_content(
                        content, field, lang_code
                    )
        return data

    def get_missing_translation(self, obj):
        lang_code = self.context.get("language_code") or "en"
        return get_verified_content(obj, lang_code) is None

    def get_available_languages(self, obj):
        return available_languages_for_topic(obj)


class LegalTopicListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.slug", read_only=True)
    available_languages = serializers.SerializerMethodField()

    class Meta:
        model = LegalTopic
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "available_languages",
        ]

    def get_available_languages(self, obj):
        return available_languages_for_topic(obj)


class SearchResultSerializer(serializers.Serializer):
    """Shape of one search result (category or topic)."""

    kind = serializers.CharField()  # "category" | "topic"
    category_slug = serializers.CharField()
    category_name = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(required=False, default="")
