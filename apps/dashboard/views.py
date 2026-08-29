from django.shortcuts import render

from apps.dashboard.services import build_dashboard


def dashboard(request):
    """Public HTML dashboard of live MANYA legal content and usage."""
    return render(request, "dashboard/index.html", build_dashboard())
