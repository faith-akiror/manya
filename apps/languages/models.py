"""Dynamic, database-driven languages for MANYA.

Languages are NEVER hardcoded. To add a language an administrator simply
creates a Language record (Django admin) — the website, APIs and USSD flows
then automatically serve it.
"""

from django.core.exceptions import ValidationError
from django.db import models


class Language(models.Model):
    """A spoken language MANYA supports.

    ``code`` uses the ISO 639-3 convention (``en``, ``lg``, ``teo``, ``ach``) so
    that codes remain consistent as MANYA grows to 50+ languages.
    """

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
