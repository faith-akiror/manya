"""Public API views for referrals."""

from django.db.models import Q
from rest_framework import generics

from apps.referrals.models import Referral
from apps.referrals.serializers import ReferralSerializer


class ReferralListAPIView(generics.ListAPIView):
    """List verified referrals with optional filters.

    Query parameters:
        category — exact category match
        location — case-insensitive contains match
        service  — case-insensitive contains match on services text
        language — ISO code; matches referrals available in that language
    """

    serializer_class = ReferralSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Referral.objects.filter(is_verified=True)
        category = self.request.query_params.get("category")
        location = self.request.query_params.get("location")
        service = self.request.query_params.get("service")
        language = self.request.query_params.get("language")

        if category:
            queryset = queryset.filter(category__icontains=category)
        if location:
            queryset = queryset.filter(
                Q(location__icontains=location) | Q(name__icontains=location)
            )
        if service:
            queryset = queryset.filter(
                Q(services__icontains=service) | Q(description__icontains=service)
            )
        if language:
            queryset = queryset.filter(languages__code=language)
        return queryset.distinct()
