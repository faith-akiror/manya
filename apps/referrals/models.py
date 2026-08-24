"""Verified referral resources (legal aid, government, professional bodies).

MANYA never fabricates contact information. Only ``is_verified`` referrals
become public.
"""

from django.db import models

from apps.languages.models import Language


class Referral(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    services = models.TextField(blank=True)
    languages = models.ManyToManyField(Language, related_name="referrals", blank=True)
    is_verified = models.BooleanField(default=False)
    last_verified = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"

    def __str__(self):
        return self.name
