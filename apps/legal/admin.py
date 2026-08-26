"""Django admin for legal content — the human verification hub.

Admins can:
- manage sources and record amendments/repeals,
- review draft content and mark it VERIFIED (only valid records can become
  VERIFIED),
- generate machine translations with Sunbird AI (always saved as DRAFT for
  human review — MANYA never automatically publishes AI output).
"""

import logging

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.utils import timezone

from apps.languages.admin import ContentTranslationGenericInline
from apps.legal.models import (
    LegalCategory,
    LegalContent,
    LegalSource,
    LegalTopic,
)
from apps.legal.services.source_service import SourceService
from apps.legal.services.translation_service import TranslationWorkflow

logger = logging.getLogger(__name__)


@admin.register(LegalSource)
class LegalSourceAdmin(admin.ModelAdmin):
    inlines = [ContentTranslationGenericInline]
    list_display = (
        "name",
        "organization",
        "source_type",
        "status",
        "authority_level",
        "is_authoritative",
        "last_verified_at",
        "next_review_date",
        "requires_review",
    )
    list_filter = (
        "source_type",
        "status",
        "authority_level",
        "is_authoritative",
    )
    search_fields = ("name", "organization", "document_title", "document_identifier")
    fieldsets = (
        (None, {"fields": ("name", "organization", "source_type", "url")}),
        (
            "Document",
            {"fields": ("document_title", "document_identifier", "chapter", "version")},
        ),
        (
            "Dates",
            {
                "fields": ("publication_date", "effective_date", "retrieved_at"),
            },
        ),
        (
            "Authority & status",
            {
                "fields": (
                    "jurisdiction",
                    "status",
                    "authority_level",
                    "is_authoritative",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "last_checked_at",
                    "last_verified_at",
                    "next_review_date",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
    )
    actions = ("mark_verified", "mark_review", "set_amended", "set_repealed")

    @admin.action(description="Mark selected sources as verified")
    def mark_verified(self, request, queryset):
        for source in queryset:
            SourceService.mark_verified(source)
        self.message_user(request, f"{queryset.count()} source(s) marked verified.")

    @admin.action(description="Mark selected sources as reviewed")
    def mark_review(self, request, queryset):
        for source in queryset:
            SourceService.mark_checked(source)
        self.message_user(request, f"{queryset.count()} source(s) marked reviewed.")

    @admin.action(description="Record: amended")
    def set_amended(self, request, queryset):
        for source in queryset:
            SourceService.record_status_change(source, "AMENDED")
        self.message_user(request, "Status set to AMENDED.")

    @admin.action(description="Record: repealed")
    def set_repealed(self, request, queryset):
        for source in queryset:
            SourceService.record_status_change(source, "REPEALED")
        self.message_user(request, "Status set to REPEALED.")


class LegalContentInline(admin.TabularInline):
    model = LegalContent
    extra = 0
    fields = ("language", "title", "verification_status", "last_verified")
    readonly_fields = ("last_verified",)


@admin.register(LegalCategory)
class LegalCategoryAdmin(admin.ModelAdmin):
    inlines = [ContentTranslationGenericInline]
    list_display = ("name", "slug", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(LegalTopic)
class LegalTopicAdmin(admin.ModelAdmin):
    inlines = [LegalContentInline, ContentTranslationGenericInline]
    list_display = ("name", "category", "slug", "is_active", "display_order")
    list_filter = ("category", "is_active")
    list_editable = ("is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(LegalContent)
class LegalContentAdmin(admin.ModelAdmin):
    inlines = [ContentTranslationGenericInline]
    list_display = (
        "title",
        "topic",
        "language",
        "verification_status",
        "last_verified",
        "updated_at",
    )
    list_filter = ("verification_status", "language", "topic__category", "topic")
    search_fields = (
        "title",
        "summary",
        "legal_reference",
        "section_reference",
        "topic__name",
    )
    autocomplete_fields = ("topic", "source", "language", "original_content")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {"fields": ("topic", "language", "source", "original_content", "title")},
        ),
        (
            "What the law says",
            {"fields": ("summary", "legal_reference", "section_reference")},
        ),
        (
            "What this means / What you can do",
            {"fields": ("what_this_means", "next_steps", "documents_required")},
        ),
        ("Rights information", {"fields": ("rights_information",)}),
        ("Source display", {"fields": ("source_title", "source_url")}),
        ("Verification", {"fields": ("verification_status", "last_verified")}),
        ("Disclaimer", {"fields": ("disclaimer",)}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    actions = ("mark_review", "mark_verified", "archive", "generate_translations")

    def lookup_allowed(self, lookup, value):
        if lookup.split("__")[0] in {"topic", "language", "source", "original_content"}:
            return True
        return super().lookup_allowed(lookup, value)

    @admin.action(description="Send selected content for review")
    def mark_review(self, request, queryset):
        queryset.update(verification_status="REVIEW")
        self.message_user(request, "Selected content moved to REVIEW.")

    @admin.action(description="Mark selected content as VERIFIED (after human review)")
    def mark_verified(self, request, queryset):
        verified = 0
        for content in queryset:
            content.verification_status = "VERIFIED"
            try:
                content.full_clean()
            except ValidationError as exc:
                self.message_user(
                    request,
                    f"'{content}' cannot be verified: {'; '.join(exc.messages)}",
                    level=messages.ERROR,
                )
                continue
            content.last_verified = timezone.now().date()
            content.save()
            if content.source:
                SourceService.mark_verified(content.source)
            verified += 1
        self.message_user(request, f"{verified} record(s) verified.")

    @admin.action(description="Archive selected content")
    def archive(self, request, queryset):
        queryset.update(verification_status="ARCHIVED")

    @admin.action(
        description="Generate Sunbird translations for selected content",
    )
    def generate_translations(self, request, queryset):
        """Two-step admin action: pick languages -> create DRAFT translations."""
        from apps.languages.models import Language

        if "language_ids" in request.POST:
            selected_ids = request.POST.getlist("language_ids")
            languages = Language.objects.filter(pk__in=selected_ids, is_active=True)
            records_created = 0
            workflow = TranslationWorkflow()
            for content in queryset:
                for language in languages:
                    try:
                        workflow.generate_translation(content, language)
                        records_created += 1
                    except Exception as exc:  # noqa: BLE001
                        self.message_user(
                            request,
                            f"'{content}' -> {language}: {exc}",
                            level=messages.WARNING,
                        )
            self.message_user(
                request,
                f"Generated {records_created} translation(s) as DRAFT. "
                "Review and verify them before publishing.",
            )
            return None

        return render(
            request,
            "admin/legal/legalcontent/translate_intermediate.html",
            {
                "contents": queryset,
                "languages": Language.active_public(),
                "action": "generate_translations",
                "selection": [str(pk) for pk in queryset.values_list("pk", flat=True)],
            },
        )
