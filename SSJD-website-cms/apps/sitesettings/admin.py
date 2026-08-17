from django.contrib import admin

from apps.sitesettings.models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Singleton — only one row, edit in place.
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
