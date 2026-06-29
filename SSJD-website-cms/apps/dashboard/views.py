from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.banners.models import Banner
from apps.branches.models import Branch
from apps.contacts.models import Contact
from apps.gallery.models import GalleryImage
from apps.notices.models import Notice
from apps.notices.serializers import NoticeSerializer
from apps.schemes.models import Scheme


class DashboardStatsView(APIView):
    """Admin dashboard summary — counts, inquiry statistics, recent notices."""
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        inquiry_by_type = list(
            Contact.objects.values("inquiry_type").annotate(count=Count("id")).order_by("-count"))
        inquiry_by_status = list(
            Contact.objects.values("status").annotate(count=Count("id")).order_by("-count"))
        recent_notices = NoticeSerializer(
            Notice.objects.all()[:5], many=True, context={"request": request}).data

        return Response({
            "totals": {
                "branches": Branch.objects.count(),
                "schemes": Scheme.objects.count(),
                "notices": Notice.objects.count(),
                "banners": Banner.objects.count(),
                "gallery_images": GalleryImage.objects.count(),
                "leads": Contact.objects.count(),
                "new_leads": Contact.objects.filter(status="new").count(),
            },
            "inquiry_statistics": {
                "by_type": inquiry_by_type,
                "by_status": inquiry_by_status,
            },
            "recent_notices": recent_notices,
            "quick_actions": [
                {"label": "Add Banner", "endpoint": "/api/v1/banners/"},
                {"label": "Add Scheme", "endpoint": "/api/v1/schemes/"},
                {"label": "Post Notice", "endpoint": "/api/v1/notices/"},
                {"label": "View Leads", "endpoint": "/api/v1/contacts/"},
            ],
        })
