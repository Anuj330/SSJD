from rest_framework import serializers

from apps.banners.models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ("id", "title", "subtitle", "image", "mobile_image",
                  "button_text", "button_link", "display_order", "is_active",
                  "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
