"""Public API views for the languages app."""

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response

from apps.languages.models import Language
from apps.languages.serializers import LanguageSerializer


class LanguageListView(generics.ListAPIView):
    """List active languages.

    The list is fully database-driven: an administrator can add a new language
    in Django admin and it will immediately appear here, on the website and in
    USSD.
    """

    serializer_class = LanguageSerializer
    pagination_class = None

    def get_queryset(self):
        return Language.active_public()


class ActiveLanguageView(generics.RetrieveAPIView):
    """Return the single active default language."""

    serializer_class = LanguageSerializer
    pagination_class = None

    def get(self, request, *args, **kwargs):
        lang = Language.get_default()
        if lang is None:
            lang = Language.active_public().first()
        serializer = self.get_serializer(lang)
        return Response(serializer.data)


@extend_schema(responses=LanguageSerializer(many=True))
class LanguageOptionsView(generics.ListAPIView):
    """Same as the list view with no pagination wrapper (convenience)."""

    serializer_class = LanguageSerializer
    pagination_class = None

    def get_queryset(self):
        return Language.active_public()
