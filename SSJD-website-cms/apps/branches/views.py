from rest_framework import viewsets

from apps.branches.models import Branch
from apps.branches.serializers import BranchSerializer
from core.permissions import IsStaffOrReadOnly


class BranchViewSet(viewsets.ModelViewSet):
    """Branch locator. Public read; staff write."""
    serializer_class = BranchSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["city", "state", "is_active"]
    search_fields = ["branch_name", "city", "state", "address"]
    ordering_fields = ["branch_name", "city", "state", "created_at"]

    def get_queryset(self):
        qs = Branch.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs
