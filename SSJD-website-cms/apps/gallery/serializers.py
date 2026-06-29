from rest_framework import serializers

from apps.gallery.models import GalleryAlbum, GalleryImage


class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ("id", "album", "title", "image", "display_order", "created_at")
        read_only_fields = ("id", "created_at")


class GalleryAlbumSerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    image_count = serializers.IntegerField(source="images.count", read_only=True)

    class Meta:
        model = GalleryAlbum
        fields = ("id", "title", "category", "event_date", "cover_image",
                  "is_active", "images", "image_count", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
