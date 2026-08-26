from django.urls import path

from apps.messaging.views import (
    IncomingSMSView,
    SMSAPIView,
    SMSDeliveryCallbackView,
)

urlpatterns = [
    path("sms/", SMSAPIView.as_view(), name="sms-send"),
    # Two-way SMS webhooks (Africa's Talking -> MANYA)
    path("sms/callback/", SMSDeliveryCallbackView.as_view(), name="sms-delivery-callback"),
    path("sms/incoming/", IncomingSMSView.as_view(), name="sms-incoming"),
]
