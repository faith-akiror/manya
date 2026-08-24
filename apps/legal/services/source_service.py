"""Source management service.

Encapsulates the rules around verifying sources, recording status changes
(amendment/repeal) and identifying sources that require review.

MANYA never automatically marks a source obsolete without review, and never
invents legal information.
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.legal.models import LegalSource

REVIEW_PERIOD_DAYS = 180  # default review cycle for a verified source


class SourceService:
    @staticmethod
    def mark_verified(source: LegalSource, verified_at=None) -> LegalSource:
        """Record that a human reviewed the source and it checks out."""
        source.last_verified_at = verified_at or timezone.now()
        source.last_checked_at = source.last_verified_at
        source.next_review_date = (
            source.last_verified_at + timedelta(days=REVIEW_PERIOD_DAYS)
        ).date()
        source.save(
            update_fields=["last_verified_at", "last_checked_at", "next_review_date"]
        )
        return source

    @staticmethod
    def mark_checked(source: LegalSource, checked_at=None) -> LegalSource:
        """Record that a human re-checked (but not necessarily verified) it."""
        source.last_checked_at = checked_at or timezone.now()
        source.save(update_fields=["last_checked_at"])
        return source

    @staticmethod
    def record_status_change(source: LegalSource, new_status: str) -> LegalSource:
        """Admin records that a law was amended/repealed/etc."""
        source.status = new_status
        source.last_checked_at = timezone.now()
        source.save(update_fields=["status", "last_checked_at"])
        return source

    @staticmethod
    def requiring_review():
        """Sources that should be reviewed now (never auto-obsoleted)."""
        from datetime import date

        return LegalSource.objects.filter(
            models.Q(next_review_date__lte=date.today())
            | models.Q(
                last_verified_at__isnull=True,
                created_at__lte=timezone.now() - timedelta(days=1),
            )
        )
