from rest_framework import serializers

from apps.notices.models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notice
        fields = ("id", "title", "slug", "description", "attachment_pdf", "thumbnail",
                  "publish_date", "expiry_date", "is_important", "is_active",
                  "is_expired", "created_at", "updated_at")
        read_only_fields = ("id", "slug", "created_at", "updated_at")
