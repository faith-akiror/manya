"""Django admin for referrals."""

from django.contrib import admin

from apps.referrals.models import Referral


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "location",
        "is_verified",
        "last_verified",
    )
    list_filter = ("is_verified", "category", "languages")
    search_fields = ("name", "description", "location", "services")
    filter_horizontal = ("languages",)
    readonly_fields = ("created_at", "updated_at")
    actions = ("verify_selected",)

    @admin.action(description="Mark selected referrals as verified")
    def verify_selected(self, request, queryset):
        from django.utils import timezone

        queryset.update(is_verified=True, last_verified=timezone.now().date())
        self.message_user(request, "Referrals marked as verified.")
