"""Serializers for SMS requests (validated before any external call)."""

from rest_framework import serializers

from apps.messaging.services.africastalking_sms import validate_phone_number


class SMSRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=30)
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    topic = serializers.CharField(max_length=160, required=False, allow_blank=True)
    language = serializers.CharField(max_length=10, required=False, allow_blank=True)

    def validate_phone_number(self, value):
        try:
            return validate_phone_number(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate(self, attrs):
        if not attrs.get("message") and not attrs.get("topic"):
            raise serializers.ValidationError("Provide either 'message' or 'topic'.")
        return attrs
