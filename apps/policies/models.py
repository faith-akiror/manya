"""Verified policy updates (government gazette, official announcements).

MANYA never fabricates policy updates. Only active, sourced entries are
public.
"""

from django.db import models


class PolicyUpdate(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    summary = models.TextField(blank=True)
    category = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)
    published_at = models.DateField(null=True, blank=True)
    last_verified = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Policy update"
        verbose_name_plural = "Policy updates"

    def __str__(self):
        return self.title
