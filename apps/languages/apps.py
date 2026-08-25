from django.apps import AppConfig
from django.db.models.signals import post_save


class LanguagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.languages"
    verbose_name = "MANYA Languages"

    def ready(self):
        from apps.languages.models import Language

        post_save.connect(self._create_ui_templates, sender=Language)

    @staticmethod
    def _create_ui_templates(sender, instance, created, **kwargs):
        if not created:
            return
        from apps.languages.models import UIMessage

        english_messages = UIMessage.objects.filter(language__code="en")
        for msg in english_messages:
            UIMessage.objects.get_or_create(
                language=instance,
                key=msg.key,
                defaults={"text": msg.text},
            )
