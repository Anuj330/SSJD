from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets

from apps.notices.models import Notice
from apps.notices.serializers import NoticeSerializer
from core.permissions import IsStaffOrReadOnly


class NoticeViewSet(viewsets.ModelViewSet):
    """News & notices. Public read shows only live (active, published, unexpired)."""
    serializer_class = NoticeSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "slug"
    filterset_fields = ["is_important", "is_active"]
    search_fields = ["title", "description"]
    ordering_fields = ["publish_date", "created_at"]

    def get_queryset(self):
        qs = Notice.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            today = timezone.now().date()
            qs = qs.filter(is_active=True, publish_date__lte=today).filter(
                Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))
        return qs
