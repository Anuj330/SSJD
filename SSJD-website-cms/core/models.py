"""Abstract base models reused across every CMS app.

BaseModel gives every record:
  * a UUID primary key (non-enumerable, safe to expose in URLs/APIs)
  * created_at / updated_at timestamps (indexed)
  * soft delete (is_deleted / deleted_at) via SoftDeleteManager
  * audit stamping (created_by / updated_by) pulled from thread-local request user
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.managers import AllObjectsManager, SoftDeleteManager
from core.middleware import get_current_user


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user is not None:
            if self._state.adding and self.created_by_id is None:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, hard=False):
        """Soft delete by default; pass hard=True to truly remove."""
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
