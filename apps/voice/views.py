"""Africa's Talking Voice callback view.

Africa's Talking POSTs call notifications to the voice callback URL
(configured under ``Voice -> Phone Numbers -> Callback``). Every notification
carries ``sessionId`` and ``isActive``; after a digit press it also carries
``dtmfDigits``. We answer with Africa's Talking Voice XML.

CSRF is bypassed: the caller is the provider, never a browser. Like the other
provider webhooks, this endpoint is deliberately NOT rate-limited — all voice
traffic arrives from Africa's Talking IPs and a per-IP cap would drop calls.
"""

import json
import logging

from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.voice.services.africastalking_voice import VoiceService
from apps.voice.services.voice_service import VoiceConversationService

logger = logging.getLogger(__name__)


def _parse_provider_payload(request) -> dict:
    """Africa's Talking may POST form-encoded or JSON; accept both."""
    raw = request.body.decode("utf-8", errors="replace") if request.body else ""
    if raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except ValueError:
            pass
    if request.POST:
        return dict(request.POST.items())
    return {}


@extend_schema(
    request={
        "application/x-www-form-urlencoded": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string"},
                "isActive": {"type": "string"},
                "direction": {"type": "string"},
                "callerNumber": {"type": "string"},
                "destinationNumber": {"type": "string"},
                "dtmfDigits": {"type": "string"},
                "callSessionState": {"type": "string"},
                "durationInSeconds": {"type": "string"},
                "currencyCode": {"type": "string"},
                "amount": {"type": "string"},
            },
        },
        "application/json": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string"},
                "isActive": {"type": "string"},
                "callerNumber": {"type": "string"},
                "destinationNumber": {"type": "string"},
                "dtmfDigits": {"type": "string"},
            },
        },
    },
    responses={
        200: {
            "description": "Africa's Talking Voice XML describing the next actions.",
            "application/xml": {
                "type": "string",
                "example": (
                    '<Response><Say voice="en-US-Standard-C">Choose your language'
                    '</Say><GetDigits numDigits="1"><Say>Please press a number'
                    "</Say></GetDigits></Response>"
                ),
            },
        }
    },
    examples=[
        OpenApiExample(
            "Call connected",
            value={
                "sessionId": "ATVOID-000001",
                "isActive": "1",
                "direction": "inbound",
                "callerNumber": "+256700000000",
                "destinationNumber": "+256700000001",
                "dtmfDigits": "",
            },
        ),
        OpenApiExample(
            "Digit pressed",
            value={
                "sessionId": "ATVOID-000001",
                "isActive": "1",
                "callerNumber": "+256700000000",
                "dtmfDigits": "1",
            },
        ),
        OpenApiExample(
            "Call ended",
            value={
                "sessionId": "ATVOID-000001",
                "isActive": "0",
                "callerNumber": "+256700000000",
                "durationInSeconds": "82",
                "currencyCode": "UGX",
                "amount": "0.1",
            },
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def voice_callback(request):
    payload = _parse_provider_payload(request)
    try:
        callback_url = request.build_absolute_uri(reverse("voice-callback"))
        result = VoiceConversationService().dispatch(payload, callback_url=callback_url)
    except Exception:  # noqa: BLE001 - the call must always end cleanly
        logger.exception(
            "Voice callback failed for session %s", payload.get("sessionId")
        )
        result = {
            "xml": VoiceService().end_response(
                "We are sorry - something went wrong. Please try again later."
            ),
            "continue_flow": False,
        }

    return HttpResponse(
        result["xml"],
        content_type="text/xml",
        status=status.HTTP_200_OK,
    )


voice_callback_view = csrf_exempt(voice_callback)
