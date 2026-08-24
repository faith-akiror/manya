"""Lightweight user preferences for SMS/USSD users.

MANYA knows a phone number and the language the person prefers — nothing
else. No national ID, no financial data, no case details.
"""

from django.db import models

from apps.languages.models import Language


class UserPreference(models.Model):
    phone_number = models.CharField(max_length=30, unique=True)
    preferred_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        related_name="user_preferences",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User preference"
        verbose_name_plural = "User preferences"

    def __str__(self):
        return f"{self.phone_number} -> {self.preferred_language or 'default'}"
