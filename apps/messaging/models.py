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


def sms_fingerprint(payload) -> str:
    """Stable hash of a provider payload for duplicate-callback protection."""
    import hashlib
    import json

    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SmsDeliveryReport(models.Model):
    """One Africa's Talking delivery-report event for an SMS MANYA sent.

    Idempotent by design: reports that carry a provider ``message_id`` are
    upserted on that id; reports without one are deduplicated by a SHA-256
    fingerprint of the raw payload, so AT re-delivering the same callback can
    never create a second record.
    """

    message_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Africa's Talking messageId, when provided.",
    )
    phone_number = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=50, blank=True)
    status_code = models.CharField(max_length=20, blank=True)
    failure_reason = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict)
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMS delivery report"
        verbose_name_plural = "SMS delivery reports"
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.phone_number}: {self.status or 'unknown'}"


class IncomingSMS(models.Model):
    """An SMS message received from a user (stored before processing).

    Deduplicated by fingerprint: Africa's Talking retrying the same incoming
    webhook is stored once and processed once.
    """

    phone_number = models.CharField(max_length=30, db_index=True)
    message_text = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    network = models.CharField(max_length=100, blank=True)
    language_code = models.CharField(
        max_length=10,
        blank=True,
        help_text="Conversation language snapshot at receipt time.",
    )
    raw_payload = models.JSONField(default=dict)
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    reply_text = models.TextField(
        blank=True,
        help_text="What MANYA replied, in the user's language.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Incoming SMS"
        verbose_name_plural = "Incoming SMS"
        ordering = ("-created_at",)

    def __str__(self):
        preview = (self.message_text or "")[:30]
        return f"{self.phone_number}: {preview}"
