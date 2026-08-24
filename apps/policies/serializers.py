"""Serializers for policy updates."""

from rest_framework import serializers

from apps.policies.models import PolicyUpdate


class PolicyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyUpdate
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "category",
            "source",
            "source_url",
            "published_at",
            "last_verified",
        ]
