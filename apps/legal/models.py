"""Legal source, category, topic and content models.

SOURCE-FIRST PRINCIPLE (see README "Verified legal sources"):
MANYA never invents legal information. Every public legal item references a
LegalSource taken from an authoritative or recognised Ugandan legal source.
"""

from django.core.exceptions import ValidationError
from django.db import models

from apps.languages.models import Language

DISCLAIMER = (
    "This information is provided for general legal and policy awareness. "
    "MANYA is not a law firm and this information does not constitute legal "
    "advice. Laws and policies may change. Always consult the original source "
    "or a qualified legal professional for advice about your specific "
    "situation."
)

LEGAL_DISCLAIMER = DISCLAIMER

SOURCE_TYPE_CHOICES = [
    ("CONSTITUTION", "Constitution"),
    ("ACT", "Act of Parliament"),
    ("AMENDMENT_ACT", "Amendment Act"),
    ("STATUTORY_INSTRUMENT", "Statutory Instrument"),
    ("REGULATION", "Regulation"),
    ("LEGAL_NOTICE", "Legal Notice"),
    ("GAZETTE", "Government Gazette"),
    ("COURT_DECISION", "Court decision"),
    ("GOVERNMENT_POLICY", "Government policy"),
    ("GOVERNMENT_GUIDELINE", "Government guideline"),
    ("ULRC_PUBLICATION", "ULRC publication"),
    ("ULII", "ULII"),
    ("OTHER_VERIFIED", "Other verified source"),
]

SOURCE_STATUS_CHOICES = (
    ("ACTIVE", "Active"),
    ("AMENDED", "Amended"),
    ("REPEALED", "Repealed"),
    ("SUPERSEDED", "Superseded"),
    ("UNCOMMENCED", "Not yet commenced"),
    ("UNKNOWN", "Unknown"),
)

AUTHORITY_LEVEL_CHOICES = (
    (1, "Level 1 — Constitution, Acts, Regulations, Official decisions"),
    (2, "Level 2 — ULII, recognised legal institutes / legal-aid bodies"),
    (3, "Level 3 — NGOs, universities, research & educational resources"),
    (4, "Level 4 — Never legal authority (blogs, social media, random sites)"),
)

VERIFICATION_STATUS_CHOICES = (
    ("DRAFT", "Draft"),
    ("REVIEW", "Review"),
    ("VERIFIED", "Verified"),
    ("ARCHIVED", "Archived"),
)


class LegalSource(models.Model):
    """A verified origin of legal information."""

    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(
        max_length=40, choices=SOURCE_TYPE_CHOICES, default="ACT"
    )
    url = models.URLField(blank=True)
    document_title = models.CharField(max_length=255, blank=True)
    document_identifier = models.CharField(max_length=255, blank=True)
    chapter = models.CharField(max_length=100, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    version = models.CharField(max_length=50, blank=True)
    jurisdiction = models.CharField(max_length=20, default="UG")
    status = models.CharField(
        max_length=20, choices=SOURCE_STATUS_CHOICES, default="ACTIVE"
    )
    authority_level = models.PositiveSmallIntegerField(
        choices=AUTHORITY_LEVEL_CHOICES, default=1
    )
    is_authoritative = models.BooleanField(default=True)
    retrieved_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Legal source"
        verbose_name_plural = "Legal sources"

    def __str__(self):
        return self.name

    @property
    def requires_review(self) -> bool:
        """Sources flagged for review (never auto-obsolete)."""
        from datetime import date

        if self.next_review_date and self.next_review_date <= date.today():
            return True
        return self.last_verified_at is None

    def status_display_message(self) -> str:
        """Public message reflecting the current status of the source."""
        if self.status == "REPEALED":
            return "This law has been repealed."
        if self.status == "AMENDED":
            return "This law has been amended. View the current version."
        if self.status == "UNCOMMENCED":
            return "This provision has not yet commenced."
        if self.status == "SUPERSEDED":
            return "This law has been superseded. View the current version."
        return ""


class LegalCategory(models.Model):
    """A broad legal area (Employment, Land, Family, ...)."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Legal category"
        verbose_name_plural = "Legal categories"

    def __str__(self):
        return self.name


class LegalTopic(models.Model):
    """A concrete issue inside a category (e.g. Unpaid salary)."""

    category = models.ForeignKey(
        LegalCategory, on_delete=models.CASCADE, related_name="topics"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Legal topic"
        verbose_name_plural = "Legal topics"

    def __str__(self):
        return self.name


class LegalContent(models.Model):
    """One version of a topic's content in one language.

    The same content record is served by the website, USSD, SMS and Voice —
    all channels read the SAME verified database.

    A record CANNOT become VERIFIED unless it has a valid source, a legal
    reference, a source URL where available and a verification date.
    """

    topic = models.ForeignKey(
        LegalTopic, on_delete=models.CASCADE, related_name="contents"
    )
    language = models.ForeignKey(
        Language, on_delete=models.PROTECT, related_name="legal_contents"
    )
    source = models.ForeignKey(
        LegalSource,
        on_delete=models.PROTECT,
        related_name="contents",
        null=True,
        blank=True,
    )
    original_content = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="translations",
        null=True,
        blank=True,
        help_text="For translations: the source content this record was translated from.",
    )

    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    rights_information = models.TextField(blank=True)
    what_this_means = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)
    documents_required = models.TextField(blank=True)

    source_title = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)
    legal_reference = models.CharField(max_length=255, blank=True)
    section_reference = models.CharField(max_length=255, blank=True)

    last_verified = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=10, choices=VERIFICATION_STATUS_CHOICES, default="DRAFT"
    )
    disclaimer = models.TextField(default=DISCLAIMER)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic__display_order", "language__code"]
        verbose_name = "Legal content"
        verbose_name_plural = "Legal content"
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "language"],
                condition=~models.Q(verification_status="ARCHIVED"),
                name="legalcontent_unique_active_topic_language",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.language.code})"

    def clean(self):
        super().clean()
        errors = {}
        if self.verification_status == "VERIFIED":
            if not self.source:
                errors["source"] = "Verified content requires a valid source."
            if not self.topic:
                errors["topic"] = "Verified content requires a topic."
            if not self.language:
                errors["language"] = "Verified content requires a language."
            if not self.legal_reference:
                errors["legal_reference"] = (
                    "Verified content requires a legal reference to the source."
                )
            if not self.last_verified:
                errors["last_verified"] = (
                    "Verified content requires a verification date."
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.source:
            self.source_title = (
                self.source_title or self.source.document_title or self.source.name
            )
            if not self.source_url and self.source.url:
                self.source_url = self.source.url
        super().save(*args, **kwargs)

    @property
    def is_public(self) -> bool:
        return self.verification_status == "VERIFIED"
