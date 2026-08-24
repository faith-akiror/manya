"""Public API views for SMS.

POST /api/sms/
Body: {"phone_number": "+256...", "message": "...", "language": "ach"}
  or  {"phone_number": "+256...", "topic": "unpaid-salary", "language": "ach"}

The Africa's Talking API is only ever touched inside SMSService; views never
call the provider directly. Failures are isolated and never expose stack
traces.
"""

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.languages.services.ui_translations import UITranslationService
from apps.legal.models import LegalTopic
from apps.legal.services.content_query import get_verified_content
from apps.messaging.models import UserPreference
from apps.messaging.serializers import SMSRequestSerializer
from apps.messaging.services.africastalking_sms import (
    SMSConfigurationError,
    SMSService,
    SMSServiceError,
    build_content_sms,
)


class SMSAPIView(APIView):
    """Send a MANYA SMS summary via Africa's Talking."""

    throttle_scope = "sms"

    @extend_schema(
        request=SMSRequestSerializer,
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}}}
        },
        examples=[
            OpenApiExample(
                "Send topic summary",
                value={
                    "phone_number": "+256700000000",
                    "topic": "unpaid-salary",
                    "language": "ach",
                },
            ),
            OpenApiExample(
                "Send custom message",
                value={
                    "phone_number": "+256700000000",
                    "message": "MANYA: Know your rights.",
                },
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = SMSRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = data["phone_number"]

        # Build message: explicit text, or a verified-content summary.
        if data.get("message"):
            message = data["message"]
        else:
            language_code = data.get("language") or "en"
            topic = LegalTopic.objects.filter(
                slug=data["topic"], is_active=True, category__is_active=True
            ).first()
            if topic is None:
                return Response(
                    {"error": "Topic not found."}, status=status.HTTP_404_NOT_FOUND
                )
            content = get_verified_content(topic, language_code)
            if content is None and language_code != "en":
                content = get_verified_content(topic, "en")
            if content is None:
                return Response(
                    {
                        "error": UITranslationService.get(
                            "missing_translation_message", language_code
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            message = build_content_sms(content)

        # Remember the phone's language preference (light-touch, no auth).
        language = None
        if data.get("language"):
            from apps.languages.models import Language

            language = Language.objects.filter(
                code=data["language"], is_active=True
            ).first()
        UserPreference.objects.update_or_create(
            phone_number=phone,
            defaults={
                "preferred_language": language or None,
            },
        )

        try:
            SMSService().send(phone, message)
        except SMSConfigurationError:
            return Response(
                {"error": "SMS service is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except SMSServiceError:
            return Response(
                {
                    "error": "We could not send the SMS right now. Please try again later."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "sent"})
