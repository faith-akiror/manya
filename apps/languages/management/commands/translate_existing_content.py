"""Translate MANYA content into a language using the Sunbird-powered service.

Backfill translations for any active language without changing code. Fully
idempotent: existing database translations are skipped, Sunbird is only called
for genuinely missing translations, and results are saved to the database so a
second run makes no new API calls.

Usage:
    python manage.py translate_existing_content --language=lg
    python manage.py translate_existing_content --language=teo Acholi
    python manage.py translate_existing_content                     # all languages
    python manage.py translate_existing_content --language=sw --dry-run
    python manage.py translate_existing_content --language=fr       # unsupported -> safe skip
"""

import logging

from django.core.management.base import BaseCommand

from apps.languages.models import Language
from apps.languages.services.translation_service import (
    TRANSLATABLE_MODELS,
    TranslationService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate missing Sunbird translations for active languages (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--language",
            action="append",
            dest="languages",
            default=None,
            help="Language code(s) to translate into. Repeatable. Default: all active.",
        )
        parser.add_argument(
            "--no-ui",
            action="store_true",
            help="Skip UI message translation (UIMessage keys).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be translated without calling Sunbird.",
        )

    def handle(self, *args, **options):
        requested = options.get("languages")
        if requested:
            languages = list(
                Language.active_public().filter(code__in=requested)
            )
            missing = [c for c in requested if c not in [l.code for l in languages]]
            for code in missing:
                self.stderr.write(f"Unknown/inactive language code: {code}. Skipping.")
        else:
            languages = list(Language.active_public().exclude(is_default=True))
            if not languages:
                languages = list(Language.active_public())

        if not languages:
            self.stdout.write(self.style.WARNING("No languages selected."))
            return

        dry_run = options["dry_run"]
        include_ui = not options["no_ui"]

        if dry_run:
            for lang in languages:
                self.stdout.write(f"[dry-run] Would translate into {lang.code} ({lang.name})")
            return

        for lang in languages:
            self.stdout.write(f"Translating into {lang.code} ({lang.name}) ...")
            stats = TranslationService.generate_missing_for_language(
                lang.code, include_ui=include_ui
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  created={stats['created']} "
                    f"skipped={stats['skipped']} failed={stats['failed']} "
                    f"(models: {', '.join(TRANSLATABLE_MODELS)})"
                )
            )