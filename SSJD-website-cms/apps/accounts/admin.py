from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.forms import UserChangeForm, UserCreationForm
from apps.accounts.models import EmailToken, User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_active", "is_staff", "email_verified")
    list_filter = ("role", "is_active", "is_staff", "email_verified")
    search_fields = ("email", "full_name", "phone")
    readonly_fields = ("created_at", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "phone", "role")}),
        ("Status", {"fields": ("is_active", "is_staff", "email_verified")}),
        ("Permissions", {"fields": ("is_superuser", "groups", "user_permissions")}),
        ("Audit", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2")}),
    )


admin.site.register(User, UserAdmin)
admin.site.register(EmailToken)

admin.site.site_header = "SSJD Cooperative — Website CMS"
admin.site.site_title = "SSJD CMS"
admin.site.index_title = "Content Management"
