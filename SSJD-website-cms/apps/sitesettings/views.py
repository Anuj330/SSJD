from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.sitesettings.models import SiteSetting
from apps.sitesettings.serializers import SiteSettingSerializer
from core.permissions import IsAdminOrReadOnly


class SiteSettingView(generics.RetrieveUpdateAPIView):
    """Single global settings object. Public read; Admin write (PUT/PATCH)."""
    serializer_class = SiteSettingSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminOrReadOnly()]

    def get_object(self):
        return SiteSetting.load()
