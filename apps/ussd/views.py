"""Africa's Talking USSD callback view.

Africa's Talking POSTs to /api/ussd/ with:
    sessionId, phoneNumber, text (what the user typed so far), networkCode, level

We return plain text: ``CON ...`` to continue or ``END ...`` to terminate.
CSRF is bypassed (the request comes from the provider, not a browser) and the
endpoint is rate-limited.
"""

import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from apps.ussd.services.ussd_service import UssdService

logger = logging.getLogger(__name__)


@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "sessionId": {"type": "string"},
                "phoneNumber": {"type": "string"},
                "text": {"type": "string"},
                "network": {"type": "string"},
                "level": {"type": "integer"},
            },
            "required": ["sessionId", "phoneNumber", "text"],
        }
    },
    responses={
        200: {
            "description": "USSD response (CON to continue, END to terminate)",
            "application/json": {
                "type": "string",
                "example": "CON Welcome to MANYA\nKnow your rights. Know your next step.",
            },
        }
    },
    examples=[
        OpenApiExample(
            "Initial request",
            value={
                "sessionId": "ATUid_000001",
                "phoneNumber": "+256700000000",
                "text": "",
                "network": "MTN",
                "level": 1,
            },
        )
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def ussd_callback(request):
    request.throttle_scope = "ussd"
    payload = request.POST.dict()
    logger.info("USSD callback payload: %s", payload)
    result = UssdService().handle(payload)
    return HttpResponse(
        result["response"],
        status=status.HTTP_200_OK,
        content_type="text/plain",
    )


ussd_callback_view = csrf_exempt(ussd_callback)
