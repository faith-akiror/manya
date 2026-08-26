"""Django admin for messaging (user preferences, two-way SMS)."""

from django.contrib import admin

from apps.messaging.models import (
    IncomingSMS,
    SmsDeliveryReport,
    UserPreference,
)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "preferred_language", "updated_at")
    list_filter = ("preferred_language",)
    search_fields = ("phone_number",)
    autocomplete_fields = ("preferred_language",)


@admin.register(IncomingSMS)
class IncomingSMSAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "message_preview",
        "language_code",
        "provider_message_id",
        "created_at",
    )
    list_filter = ("language_code", "created_at")
    search_fields = ("phone_number", "message_text", "provider_message_id")
    readonly_fields = (
        "phone_number",
        "message_text",
        "provider_message_id",
        "network",
        "language_code",
        "raw_payload",
        "fingerprint",
        "created_at",
    )

    @admin.display(description="Message")
    def message_preview(self, obj):
        return (obj.message_text or "")[:60]


@admin.register(SmsDeliveryReport)
class SmsDeliveryReportAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "status",
        "status_code",
        "failure_reason_short",
        "message_id",
        "updated_at",
    )
    list_filter = ("status", "updated_at")
    search_fields = ("phone_number", "message_id", "failure_reason")
    readonly_fields = (
        "message_id",
        "phone_number",
        "status",
        "status_code",
        "failure_reason",
        "raw_payload",
        "fingerprint",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Failure reason")
    def failure_reason_short(self, obj):
        return (obj.failure_reason or "")[:60]
