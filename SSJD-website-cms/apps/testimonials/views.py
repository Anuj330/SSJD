from rest_framework import viewsets

from apps.testimonials.models import Testimonial
from apps.testimonials.serializers import TestimonialSerializer
from core.permissions import IsStaffOrReadOnly


class TestimonialViewSet(viewsets.ModelViewSet):
    """Customer testimonials. Public read; staff write."""
    serializer_class = TestimonialSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["rating", "is_active"]
    search_fields = ["customer_name", "review"]
    ordering_fields = ["display_order", "rating", "created_at"]

    def get_queryset(self):
        qs = Testimonial.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs
