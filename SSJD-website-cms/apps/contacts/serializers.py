from rest_framework import serializers

from apps.contacts.models import Contact


class ContactCreateSerializer(serializers.ModelSerializer):
    """Public-facing contact-form submission."""

    class Meta:
        model = Contact
        fields = ("id", "name", "phone", "email", "message", "inquiry_type")
        read_only_fields = ("id",)


class ContactSerializer(serializers.ModelSerializer):
    """Staff-facing lead view (full record)."""
    inquiry_type_display = serializers.CharField(source="get_inquiry_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Contact
        fields = ("id", "name", "phone", "email", "message", "inquiry_type",
                  "inquiry_type_display", "status", "status_display", "source",
                  "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "source")
