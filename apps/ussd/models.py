from django.db import models


class UssdSession(models.Model):
    """In-memory-persisted USSD session so the flow survives each request.

    Africa's Talking sends one request per user keystroke. Store:
    session id, phone number, selected language and current menu.

    The same state machine also powers two-way SMS conversations: an SMS
    user gets a stable session_id of ``sms:<phone>`` so their journey and
    language persist across replies, exactly like a USSD session.
    """

    CHANNEL_CHOICES = [
        ("ussd", "USSD"),
        ("sms", "SMS"),
        ("voice", "Voice"),
    ]

    session_id = models.CharField(max_length=64, unique=True)
    phone_number = models.CharField(max_length=30, blank=True)
    language_code = models.CharField(max_length=10, default="en")
    menu = models.CharField(max_length=64, blank=True)
    data = models.JSONField(default=dict, blank=True)
    channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default="ussd",
        help_text="Which channel created this conversation.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "USSD session"
        verbose_name_plural = "USSD sessions"
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.session_id} ({self.phone_number})"
