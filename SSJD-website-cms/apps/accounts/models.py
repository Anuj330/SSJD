import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"
    CONTENT_MANAGER = "content_manager", "Content Manager"
    BRANCH_MANAGER = "branch_manager", "Branch Manager"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.CONTENT_MANAGER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True, help_text="Can access the admin CMS.")
    email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["full_name", "email"]

    def __str__(self):
        return f"{self.full_name or self.email} ({self.get_role_display()})"

    @property
    def has_admin_rights(self):
        """Admin / Super Admin — may manage users and all content."""
        return self.is_superuser or self.role in (Role.SUPER_ADMIN, Role.ADMIN)


class EmailToken(models.Model):
    """One-time tokens for email verification and password reset."""

    class Purpose(models.TextChoices):
        VERIFY_EMAIL = "verify_email", "Verify email"
        RESET_PASSWORD = "reset_password", "Reset password"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["token", "purpose"])]

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def consume(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
