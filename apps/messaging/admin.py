"""Django admin for messaging (user preferences)."""

from django.contrib import admin

from apps.messaging.models import UserPreference


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "preferred_language", "updated_at")
    list_filter = ("preferred_language",)
    search_fields = ("phone_number",)
    autocomplete_fields = ("preferred_language",)
