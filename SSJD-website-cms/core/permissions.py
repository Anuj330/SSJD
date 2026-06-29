"""Role-based DRF permissions.

Roles (apps.accounts.models.Role):
    SUPER_ADMIN, ADMIN, CONTENT_MANAGER, BRANCH_MANAGER

Most CMS content is publicly *readable* (the website consumes it) but only
staff with the right role may write. `IsStaffOrReadOnly` is the workhorse used
by the content viewsets.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """Anyone can read; authenticated staff (any CMS role) can write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAdminOrReadOnly(BasePermission):
    """Read for all; write only for Admin / Super Admin."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return bool(u and u.is_authenticated and u.has_admin_rights)


class HasRole(BasePermission):
    """Generic role gate. Set `required_roles = [...]` on the view."""

    def has_permission(self, request, view):
        required = getattr(view, "required_roles", None)
        if not required:
            return True
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or u.role in required))
