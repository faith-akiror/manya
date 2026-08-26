"""Django admin for policy updates."""

from django.contrib import admin

from apps.languages.admin import ContentTranslationGenericInline
from apps.policies.models import PolicyUpdate


@admin.register(PolicyUpdate)
class PolicyUpdateAdmin(admin.ModelAdmin):
    inlines = [ContentTranslationGenericInline]
    list_display = (
        "title",
        "category",
        "source",
        "published_at",
        "last_verified",
        "is_active",
    )
    list_filter = ("is_active", "category")
    list_editable = ("is_active",)
    search_fields = ("title", "summary", "source")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
