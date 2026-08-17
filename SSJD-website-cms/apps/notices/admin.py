from django.contrib import admin

from apps.notices.models import Notice
from core.admin import BaseModelAdmin


@admin.register(Notice)
class NoticeAdmin(BaseModelAdmin):
    list_display = ("title", "publish_date", "expiry_date", "is_important", "is_active", "is_expired")
    list_editable = ("is_important", "is_active")
    list_filter = ("is_important", "is_active", "publish_date")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = BaseModelAdmin.readonly_fields + ("is_expired",)
