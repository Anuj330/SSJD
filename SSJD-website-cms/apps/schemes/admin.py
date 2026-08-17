from django.contrib import admin

from apps.schemes.models import Scheme
from core.admin import BaseModelAdmin


@admin.register(Scheme)
class SchemeAdmin(BaseModelAdmin):
    list_display = ("scheme_name", "scheme_type", "interest_rate", "is_featured", "is_active")
    list_editable = ("is_featured", "is_active")
    list_filter = ("scheme_type", "is_featured", "is_active")
    search_fields = ("scheme_name", "description")
