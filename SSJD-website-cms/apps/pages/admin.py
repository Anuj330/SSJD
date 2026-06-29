from django.contrib import admin

from apps.pages.models import Page
from core.admin import BaseModelAdmin


@admin.register(Page)
class PageAdmin(BaseModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    list_editable = ("is_published",)
    list_filter = ("is_published",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
