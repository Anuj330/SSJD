from django.contrib import admin

from apps.contacts.models import Contact
from core.admin import BaseModelAdmin


@admin.register(Contact)
class ContactAdmin(BaseModelAdmin):
    list_display = ("name", "phone", "inquiry_type", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("inquiry_type", "status", "created_at")
    search_fields = ("name", "phone", "email", "message")
    readonly_fields = BaseModelAdmin.readonly_fields + ("name", "phone", "email", "message", "inquiry_type", "source")
