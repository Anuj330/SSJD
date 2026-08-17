from django.contrib import admin

from apps.branches.models import Branch
from core.admin import BaseModelAdmin


@admin.register(Branch)
class BranchAdmin(BaseModelAdmin):
    list_display = ("branch_name", "city", "state", "phone", "is_active")
    list_editable = ("is_active",)
    list_filter = ("state", "city", "is_active")
    search_fields = ("branch_name", "city", "state", "address")
    autocomplete_fields = ("branch_manager",)
