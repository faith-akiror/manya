"""Database-driven language and translation models for MANYA."""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


class Language(models.Model):
    """A spoken language MANYA supports."""

    code = models.CharField("ISO language code", max_length=10, unique=True)
    name = models.CharField("Language name", max_length=100)
    native_name = models.CharField("Native name", max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="languages_single_default",
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.is_default:
            others = Language.objects.filter(is_default=True).exclude(pk=self.pk)
            if others.exists():
                raise ValidationError("Only one default language is allowed.")

    def save(self, *args, **kwargs):
        if self.is_default:
            Language.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)

    @classmethod
    def active_public(cls):
        """Active languages ordered for public display."""
        return cls.objects.filter(is_active=True)

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_active=True, is_default=True).first()


class UIMessage(models.Model):
    """Translated interface strings (menus, buttons, labels).

    Interface text is separate from legal content translations. Admin can add
    any key for any language without changing code.
    """

    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="ui_messages"
    )
    key = models.CharField(max_length=100)
    text = models.CharField(max_length=300)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "UI message"
        verbose_name_plural = "UI messages"
        constraints = [
            models.UniqueConstraint(
                fields=["language", "key"], name="ui_message_unique_per_language"
            )
        ]
        ordering = ["language__display_order", "language__code", "key"]

    def __str__(self):
        return f"{self.language.code}:{self.key}"


# Provenance of a ContentTranslation record. ``sunbird`` records are generated
# automatically by the translation service and may be reviewed by an admin.
TRANSLATION_SOURCE_CHOICES = [
    ("manual", "Manual"),
    ("sunbird", "Sunbird"),
    ("system", "System"),
]

# Review lifecycle of a ContentTranslation record. Machine translations start
# as ``machine_translated`` until a human marks them ``reviewed``.
TRANSLATION_STATUS_CHOICES = [
    ("machine_translated", "Machine translated"),
    ("reviewed", "Reviewed"),
]


class ContentTranslation(models.Model):
    """Generic verified translation of database content.

    MANYA can translate legal categories, topics, legal content, referrals,
    policies, and future models without changing Python code when a new
    language is added.
    """

    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="content_translations"
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="manya_translations"
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    field = models.CharField(
        max_length=100,
        help_text="Database field being translated, e.g. name, rights_information.",
    )
    text = models.TextField()
    is_verified = models.BooleanField(
        default=False,
        help_text="Only verified translations should be shown publicly.",
    )

    translation_source = models.CharField(
        max_length=20,
        choices=TRANSLATION_SOURCE_CHOICES,
        default="manual",
        help_text="Where this translation came from (Sunbird, admin, system).",
    )

    translation_status = models.CharField(
        max_length=20,
        choices=TRANSLATION_STATUS_CHOICES,
        default="machine_translated",
        help_text=(
            "Machine translations must be reviewed by a human before they "
            "should be treated as authoritative."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Content translation"
        verbose_name_plural = "Content translations"
        constraints = [
            models.UniqueConstraint(
                fields=["language", "content_type", "object_id", "field"],
                name="unique_content_translation",
            )
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id", "language", "field"])
        ]

    def __str__(self):
        return (
            f"{self.language.code}:"
            f"{self.content_type.app_label}."
            f"{self.content_type.model}:"
            f"{self.object_id}:"
            f"{self.field}"
        )


class Translation(models.Model):
    """Database-backed translation cache for free text.

    Keyed by a hash of the source text plus the language pair so that a given
    English string is translated at most once per target language. USSD/API
    lookups hit this table first and only fall through to Sunbird when the
    cache is empty — this is what keeps Sunbird API usage to one call per
    missing translation instead of one call per request.
    """

    source_text = models.TextField()
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    translated_text = models.TextField()
    source_hash = models.CharField(max_length=64, db_index=True)

    # Optional provenance: which model/record the text came from. Purely
    # informational - identical source texts share one cached translation.
    content_type = models.CharField(max_length=100, blank=True, null=True)
    content_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Translation cache"
        verbose_name_plural = "Translation cache"
        constraints = [
            models.UniqueConstraint(
                fields=["source_hash", "source_language", "target_language"],
                name="translation_cache_unique",
            )
        ]

    def __str__(self):
        return (
            f"{self.source_language}->{self.target_language} ({self.source_hash[:8]})"
        )
