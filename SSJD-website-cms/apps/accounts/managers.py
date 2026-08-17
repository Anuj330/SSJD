from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Email-based user manager."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password, **extra):
        from apps.accounts.models import Role
        extra.update(is_staff=True, is_superuser=True, is_active=True,
                     email_verified=True, role=Role.SUPER_ADMIN)
        return self._create_user(email, password, **extra)
