from django.urls import path

from apps.referrals.views import ReferralListAPIView

urlpatterns = [
    path("", ReferralListAPIView.as_view(), name="referral-list"),
]
