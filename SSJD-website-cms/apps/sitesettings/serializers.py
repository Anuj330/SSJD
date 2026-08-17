from rest_framework import serializers

from apps.sitesettings.models import SiteSetting


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        exclude = ()
        read_only_fields = ("id", "updated_at")
