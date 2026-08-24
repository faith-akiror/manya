"""Django admin for the languages app."""

from django.contrib import admin

from apps.languages.models import Language, UIMessage


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
