"""Voice callback view (MVP placeholder).

Accepts an Africa's Talking Voice payload, resolves a MANYA message for the
session and returns a deterministic action. Failures are isolated.
"""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.voice.services.africastalking_voice import VoiceService

logger = logging.getLogger(__name__)


@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string"},
                "callerNumber": {"type": "string"},
                "text": {"type": "string"},
            },
        }
    },
    responses={
        200: {
            "type": "string",
            "example": "<Speak><Say>Welcome to MANYA.</Say></Speak>",
        }
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def voice_callback(request):
    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        payload = {}
    try:
        response = VoiceService().say(
            "Welcome to MANYA. Know your rights. Know your next step.",
            requester=payload.get("callNumber"),
        )
        return HttpResponse(
            response, content_type="text/plain", status=status.HTTP_200_OK
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Voice callback failed: %s", exc)
        return JsonResponse(
            {"error": "Voice service is not available right now."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


voice_callback_view = csrf_exempt(voice_callback)
