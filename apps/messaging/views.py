"""Public API views for SMS.

POST /api/sms/
Body: {"phone_number": "+256...", "message": "...", "language": "ach"}
  or  {"phone_number": "+256...", "topic": "unpaid-salary", "language": "ach"}

The Africa's Talking API is only ever touched inside SMSService; views never
call the provider directly. Failures are isolated and never expose stack
traces.
"""

import logging

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

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
from apps.messaging.services.sms_service import normalize_sms_phone


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


# ---------------------------------------------------------------------------
# Two-way SMS webhooks (Africa's Talking -> MANYA)
#
# These are machine-to-machine callbacks: no authentication is possible and
# CSRF does not apply (DRF APIView dispatch is CSRF-exempt). Security comes
# from strict payload validation, idempotent storage and never reflecting
# internals back to the caller.
# ---------------------------------------------------------------------------
def _parse_provider_payload(request):
    """Return a list of payload dicts, or ``None`` if fully unparseable.

    Africa's Talking sends JSON for delivery reports and either JSON or
    form-encoded data for incoming messages; both are accepted here.
    """
    import json

    raw = request.body.decode("utf-8", errors="replace") if request.body else ""
    data = None
    if raw.strip():
        try:
            data = json.loads(raw)
        except ValueError:
            data = None
    if data in (None, "", {}):
        if request.POST:
            data = dict(request.POST.items())
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and data:
        return [data]
    return None


class SMSDeliveryCallbackView(APIView):
    """Receive Africa's Talking delivery reports for SMS MANYA sent.

    POST /api/messaging/sms/callback/

    Deliberately NOT rate-limited: these are provider-to-machine callbacks
    for all users combined; a per-IP limit would drop legitimate reports.
    """

    def post(self, request, *args, **kwargs):
        from apps.messaging.models import SmsDeliveryReport, sms_fingerprint

        entries = _parse_provider_payload(request)
        if entries is None:
            return Response(
                {"error": "Unparseable payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stored = 0
        duplicates = 0
        for entry in entries:
            fingerprint = sms_fingerprint(entry)
            message_id = str(entry.get("id") or entry.get("messageId") or "")
            phone = normalize_sms_phone(entry.get("phoneNumber") or "")
            fields = {
                "phone_number": phone,
                "status": str(entry.get("status") or "")[:50],
                "status_code": str(entry.get("statusCode") or "")[:20],
                "failure_reason": str(entry.get("failureReason") or ""),
                "raw_payload": entry,
                "fingerprint": fingerprint,
            }

            # 1) Already seen this exact callback? Idempotently ignore it.
            if SmsDeliveryReport.objects.filter(fingerprint=fingerprint).exists():
                duplicates += 1
                continue
            # 2) Same provider message id? Update the existing report in place
            #    (AT sends one callback per status transition).
            existing_by_id = None
            if message_id:
                existing_by_id = (
                    SmsDeliveryReport.objects.filter(message_id=message_id)
                    .order_by("-updated_at")
                    .first()
                )
            try:
                if existing_by_id:
                    for field, value in fields.items():
                        setattr(existing_by_id, field, value)
                    existing_by_id.save()
                else:
                    SmsDeliveryReport.objects.create(
                        message_id=message_id or None, **fields
                    )
                stored += 1
            except Exception as exc:  # noqa: BLE001 - duplicate race / bad field
                logger.warning(
                    "Delivery report not stored (likely duplicate): %s", exc
                )
                duplicates += 1

        logger.info(
            "SMS delivery callbacks processed: stored=%s duplicates=%s",
            stored,
            duplicates,
        )
        return Response({"status": "processed"})


class IncomingSMSView(APIView):
    """Receive SMS messages sent by users to MANYA.

    POST /api/messaging/sms/incoming/

    Not throttled per-IP: all of Africa's Talking's traffic arrives from a
    small set of provider IPs. Abuse protection comes from payload
    validation and idempotent storage instead.
    """

    def post(self, request, *args, **kwargs):
        from apps.messaging.models import IncomingSMS, sms_fingerprint
        from apps.messaging.services.sms_service import SmsConversationService

        entries = _parse_provider_payload(request)
        if entries is None:
            return Response(
                {"error": "Unparseable payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = SmsConversationService()
        processed = 0
        for entry in entries:
            fingerprint = sms_fingerprint(entry)

            # Duplicate protection first: provider retries must not
            # double-process a user's message.
            if IncomingSMS.objects.filter(fingerprint=fingerprint).exists():
                continue

            phone = normalize_sms_phone(
                entry.get("from") or entry.get("source") or ""
            )
            text = str(entry.get("text") or "")

            try:
                from apps.messaging.services.africastalking_sms import (
                    validate_phone_number,
                )

                phone = validate_phone_number(phone)
            except Exception as exc:  # noqa: BLE001 - malformed sender field
                logger.warning("Incoming SMS skipped, invalid sender: %s", exc)
                continue

            incoming, created = IncomingSMS.objects.get_or_create(
                fingerprint=fingerprint,
                defaults={
                    "phone_number": phone,
                    "message_text": text,
                    "provider_message_id": str(entry.get("id") or "")[:100],
                    "network": str(entry.get("network") or "")[:100],
                    "raw_payload": entry,
                },
            )
            if not created:
                continue

            result = conversation.process_incoming(phone, text)
            incoming.reply_text = result.get("reply", "")
            incoming.save(update_fields=["reply_text"])
            processed += 1

        logger.info("Incoming SMS processed: %s message(s)", processed)
        return Response({"status": "processed"})
