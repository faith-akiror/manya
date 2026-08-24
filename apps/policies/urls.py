from django.urls import path

from apps.policies.views import PolicyDetailAPIView, PolicyListAPIView

urlpatterns = [
    path("", PolicyListAPIView.as_view(), name="policy-list"),
    path("<slug:slug>/", PolicyDetailAPIView.as_view(), name="policy-detail"),
]
