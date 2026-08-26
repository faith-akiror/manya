"""Django admin for the MANYA languages app."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from apps.languages.models import (
    ContentTranslation,
    Language,
    Translation,
    UIMessage,
)


class ContentTranslationGenericInline(GenericTabularInline):
    """Edit translations directly on the owning legal object's admin page.

    Works for any model with a GenericRelation-free generic relation to
    ContentTranslation (content_type + object_id). Administrators pick any
    ACTIVE language from the dropdown - including languages added later -
    so the interface dynamically supports future languages with no code
    changes.
    """

    model = ContentTranslation
    extra = 0
    fields = (
        "language",
        "field",
        "text",
        "is_verified",
        "translation_source",
        "translation_status",
    )
    autocomplete_fields = ("language",)
    verbose_name = "Translation"
    verbose_name_plural = (
        "Translations (choose language + field, e.g. name / title / summary)"
    )


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Administrators manage languages without any code changes."""

    list_display = (
        "code",
        "name",
        "native_name",
        "display_order",
        "is_active",
        "is_default",
    )
    list_editable = ("display_order", "is_active", "is_default")
    list_filter = ("is_active", "is_default")
    search_fields = ("code", "name", "native_name")
    ordering = ("display_order", "name")
    actions = ("activate_selected", "deactivate_selected")

    @admin.action(description="Activate selected languages")
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected languages")
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(UIMessage)
class UIMessageAdmin(admin.ModelAdmin):
    list_display = ("key", "language", "text")
    list_filter = ("language",)
    search_fields = ("key", "text")
    autocomplete_fields = ("language",)
    ordering = ("language__display_order", "key")


@admin.register(ContentTranslation)
class ContentTranslationAdmin(admin.ModelAdmin):
    list_display = (
        "content_type",
        "object_id",
        "field",
        "language",
        "is_verified",
        "translation_source",
        "translation_status",
    )
    list_filter = (
        "language",
        "content_type",
        "field",
        "is_verified",
        "translation_source",
        "translation_status",
    )
    search_fields = ("text", "field")
    autocomplete_fields = ("language",)
    list_editable = (
        "is_verified",
        "translation_status",
    )
    ordering = ("language", "content_type", "object_id", "field")
    actions = ("mark_reviewed",)

    @admin.action(description="Mark selected translations as reviewed (human-approved)")
    def mark_reviewed(self, request, queryset):
        queryset.update(translation_status="reviewed")
        self.message_user(
            request,
            f"{queryset.count()} translation(s) marked reviewed.",
        )


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    """Translation cache — free-text Sunbird results stored per language pair."""

    list_display = (
        "source_language",
        "target_language",
        "source_preview",
        "translated_preview",
        "updated_at",
    )
    list_filter = ("source_language", "target_language")
    search_fields = ("source_text", "translated_text")
    readonly_fields = (
        "source_text",
        "source_language",
        "target_language",
        "translated_text",
        "source_hash",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)

    @admin.display(description="Source")
    def source_preview(self, obj):
        return (obj.source_text or "")[:80]

    @admin.display(description="Translated")
    def translated_preview(self, obj):
        return (obj.translated_text or "")[:80]
