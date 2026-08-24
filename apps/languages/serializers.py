"""Serializers for the languages app."""

from rest_framework import serializers

from apps.languages.models import Language, UIMessage


class LanguageSerializer(serializers.ModelSerializer):
    """Public language representation (active languages only)."""

    class Meta:
        model = Language
        fields = ["code", "name", "native_name"]


class LanguageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "code",
            "name",
            "native_name",
            "is_active",
            "is_default",
            "display_order",
        ]


class UIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UIMessage
        fields = ["id", "language", "key", "text"]
