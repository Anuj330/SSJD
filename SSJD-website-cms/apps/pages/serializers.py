from rest_framework import serializers

from apps.pages.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ("id", "title", "slug", "content", "featured_image",
                  "meta_title", "meta_description", "is_published",
                  "created_at", "updated_at")
        read_only_fields = ("id", "slug", "created_at", "updated_at")
