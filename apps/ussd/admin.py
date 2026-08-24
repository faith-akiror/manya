"""Django admin for USSD sessions (debug/monitoring only)."""

from django.contrib import admin

from apps.ussd.models import UssdSession


@admin.register(UssdSession)
class UssdSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "phone_number", "language_code", "menu", "updated_at")
    list_filter = ("language_code", "menu")
    search_fields = ("session_id", "phone_number")
    readonly_fields = ("data",)
