"""Managers implementing soft-delete semantics."""
from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """Bulk soft-delete."""
        from django.utils import timezone
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Default manager — hides soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Escape hatch — includes soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)
