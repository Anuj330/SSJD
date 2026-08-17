"""Shared admin base classes."""
from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """Common admin behaviour for BaseModel subclasses.

    * created_by/updated_by/timestamps are read-only (set automatically)
    * soft-deleted rows are hidden by default; a filter + restore action expose them
    """
    readonly_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
    actions = ("soft_delete_selected", "restore_selected")

    def get_queryset(self, request):
        return self.model.all_objects.all()

    @admin.action(description="Soft delete selected")
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, f"{queryset.count()} record(s) soft-deleted.")

    @admin.action(description="Restore selected")
    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} record(s) restored.")
