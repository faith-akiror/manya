"""Serializers for referrals (verified only at the view layer)."""

from rest_framework import serializers

from apps.referrals.models import Referral


class ReferralSerializer(serializers.ModelSerializer):
    languages = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="code"
    )

    class Meta:
        model = Referral
        fields = [
            "id",
            "name",
            "description",
            "category",
            "location",
            "phone",
            "email",
            "website",
            "services",
            "languages",
            "last_verified",
        ]
