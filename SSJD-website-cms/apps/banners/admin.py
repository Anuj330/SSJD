from django.contrib import admin
from django.utils.html import format_html

from apps.banners.models import Banner
from core.admin import BaseModelAdmin


@admin.register(Banner)
class BannerAdmin(BaseModelAdmin):
    list_display = ("title", "thumb", "display_order", "is_active", "updated_at")
    list_editable = ("display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")

    @admin.display(description="Preview")
    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:6px"/>', obj.image.url)
        return "—"
