from django.urls import path

from apps.messaging.views import SMSAPIView

urlpatterns = [
    path("sms/", SMSAPIView.as_view(), name="sms-send"),
]
