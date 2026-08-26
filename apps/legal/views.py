"""Public API views for the legal app.

MANYA returns ONLY public, verified, active information through these views.
Draft / review content is never exposed publicly.
"""

from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.legal.models import LegalCategory, LegalTopic
from apps.legal.serializers import (
    LegalCategoryDetailSerializer,
    LegalCategorySerializer,
    LegalTopicDetailSerializer,
    LegalTopicListSerializer,
)


class CategoryListAPIView(generics.ListAPIView):
    """All active legal categories (with verified topic counts)."""

    serializer_class = LegalCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return (
            LegalCategory.objects.filter(is_active=True)
            .annotate(
                topic_count=Count(
                    "topics",
                    filter=Q(topics__is_active=True)
                    & Q(topics__contents__verification_status="VERIFIED"),
                    distinct=True,
                )
            )
            .order_by("display_order", "name")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Database-only translation fast path (see serializer docstring).
        context["language_code"] = self.request.query_params.get("lang", "")
        return context


class CategoryDetailAPIView(generics.RetrieveAPIView):
    """One category with its verified topics."""

    serializer_class = LegalCategoryDetailSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return LegalCategory.objects.filter(is_active=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Full translation service path (DB -> Sunbird -> English).
        context["language_code"] = self.request.query_params.get("lang", "en")
        return context


class TopicListAPIView(generics.ListAPIView):
    """All active topics (any category) that have verified content."""

    serializer_class = LegalTopicListSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            LegalTopic.objects.filter(
                is_active=True,
                category__is_active=True,
                contents__verification_status="VERIFIED",
            )
            .distinct()
            .order_by("category__display_order", "display_order")
        )


class TopicDetailAPIView(generics.RetrieveAPIView):
    """One topic with content resolved for ``?lang=<code>``.

    If there is no verified content in the requested language the topic's
    English content is sent back *in addition to* ``missing_translation: True``
    so the website can show the "not yet available in your language" card.
    """

    serializer_class = LegalTopicDetailSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return LegalTopic.objects.filter(is_active=True, category__is_active=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["language_code"] = self.request.query_params.get("lang", "en")
        return context


class TopicSearchAPIView(APIView):
    """Search categories, topics, keywords and legal references.

    Query:
        GET /api/legal/search/?q=unpaid salary
    """

    pagination_class = None

    def get(self, request, *args, **kwargs):
        query = (request.query_params.get("q") or "").strip()
        if not query:
            return Response({"query": "", "results": []})

        # Categories whose name matches
        categories = list(
            LegalCategory.objects.filter(
                is_active=True, name__icontains=query
            ).order_by("display_order")
        )

        # Topics matching by name, description or content keyword/reference
        topic_qs = (
            LegalTopic.objects.filter(
                is_active=True,
                category__is_active=True,
                contents__verification_status="VERIFIED",
            )
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(contents__title__icontains=query)
                | Q(contents__summary__icontains=query)
                | Q(contents__legal_reference__icontains=query)
                | Q(contents__section_reference__icontains=query)
            )
            .distinct()
            .order_by("category__display_order", "display_order")
        )

        results = []
        for category in categories:
            results.append(
                {
                    "kind": "category",
                    "category_slug": category.slug,
                    "category_name": category.name,
                    "slug": category.slug,
                    "name": category.name,
                    "description": category.description,
                }
            )
        for topic in topic_qs:
            if any(r["slug"] == topic.slug and r["kind"] == "topic" for r in results):
                continue
            results.append(
                {
                    "kind": "topic",
                    "category_slug": topic.category.slug,
                    "category_name": topic.category.name,
                    "slug": topic.slug,
                    "name": topic.name,
                    "description": topic.description,
                }
            )
        return Response({"query": query, "results": results})
