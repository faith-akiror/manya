"""Root URL configuration for MANYA."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def api_home(request):
    return JsonResponse(
        {
            "name": "MANYA API",
            "tagline": "Know your rights. Know your next step.",
            "message": "Verified Ugandan legal and policy information — web, USSD, SMS, Voice.",
            "docs": "/api/docs/",
            "schema": "/api/schema/",
        }
    )


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", api_home, name="api-home"),
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    # Public API
    path("api/languages/", include("apps.languages.urls")),
    path("api/legal/", include("apps.legal.urls")),
    path("api/referrals/", include("apps.referrals.urls")),
    path("api/policies/", include("apps.policies.urls")),
    # Africa's Talking channels
    path("api/", include("apps.ussd.urls")),
    path("api/", include("apps.messaging.urls")),
    path("api/", include("apps.voice.urls")),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
