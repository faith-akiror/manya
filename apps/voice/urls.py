from django.urls import path

from apps.voice.views import voice_callback_view

urlpatterns = [
    path("voice/", voice_callback_view, name="voice-callback"),
]
