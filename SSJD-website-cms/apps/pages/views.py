from rest_framework import viewsets

from apps.pages.models import Page
from apps.pages.serializers import PageSerializer
from core.permissions import IsStaffOrReadOnly


class PageViewSet(viewsets.ModelViewSet):
    """CMS pages. Looked up by slug. Public read shows only published pages."""
    serializer_class = PageSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "slug"
    search_fields = ["title", "content"]
    ordering_fields = ["title", "created_at"]

    def get_queryset(self):
        qs = Page.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_published=True)
        return qs
