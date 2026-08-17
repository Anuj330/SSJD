from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.banners.models import Banner
from apps.banners.serializers import BannerSerializer
from core.permissions import IsStaffOrReadOnly


class BannerViewSet(viewsets.ModelViewSet):
    """Hero slider banners. Public read; staff write. Supports reordering."""
    serializer_class = BannerSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["is_active"]
    search_fields = ["title", "subtitle"]
    ordering_fields = ["display_order", "created_at"]

    def get_queryset(self):
        qs = Banner.objects.all()
        # Anonymous/website callers only see active banners.
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        """Body: {"order": ["<banner_id>", ...]} — sets display_order by position."""
        ids = request.data.get("order", [])
        for position, banner_id in enumerate(ids):
            Banner.objects.filter(id=banner_id).update(display_order=position)
        return Response({"detail": f"Reordered {len(ids)} banners."})
