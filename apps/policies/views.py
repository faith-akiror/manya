"""Public API views for policy updates."""

from rest_framework import generics

from apps.policies.models import PolicyUpdate
from apps.policies.serializers import PolicyUpdateSerializer


class PolicyListAPIView(generics.ListAPIView):
    """List active, verified policy updates (newest first)."""

    serializer_class = PolicyUpdateSerializer
    pagination_class = None

    def get_queryset(self):
        return PolicyUpdate.objects.filter(is_active=True)


class PolicyDetailAPIView(generics.RetrieveAPIView):
    """One active policy update by slug."""

    serializer_class = PolicyUpdateSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return PolicyUpdate.objects.filter(is_active=True)
