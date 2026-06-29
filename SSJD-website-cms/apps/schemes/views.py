from rest_framework import viewsets

from apps.schemes.models import Scheme
from apps.schemes.serializers import SchemeSerializer
from core.permissions import IsStaffOrReadOnly


class SchemeViewSet(viewsets.ModelViewSet):
    """FD / RD / Savings / Loan schemes. Public read; staff write."""
    serializer_class = SchemeSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["scheme_type", "is_featured", "is_active"]
    search_fields = ["scheme_name", "description"]
    ordering_fields = ["interest_rate", "minimum_amount", "scheme_name", "created_at"]

    def get_queryset(self):
        qs = Scheme.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs
