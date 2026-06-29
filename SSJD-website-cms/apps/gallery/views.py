from rest_framework import viewsets

from apps.gallery.models import GalleryAlbum, GalleryImage
from apps.gallery.serializers import GalleryAlbumSerializer, GalleryImageSerializer
from core.permissions import IsStaffOrReadOnly


class GalleryAlbumViewSet(viewsets.ModelViewSet):
    """Event galleries / albums. Public read; staff write."""
    serializer_class = GalleryAlbumSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["category", "is_active"]
    search_fields = ["title", "category"]
    ordering_fields = ["event_date", "created_at"]

    def get_queryset(self):
        qs = GalleryAlbum.objects.prefetch_related("images")
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class GalleryImageViewSet(viewsets.ModelViewSet):
    """Individual images within albums (supports multiple uploads)."""
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["album"]
    ordering_fields = ["display_order", "created_at"]
