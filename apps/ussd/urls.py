from django.urls import path

from apps.ussd.views import ussd_callback_view

urlpatterns = [
    path("ussd/", ussd_callback_view, name="ussd-callback"),
]
