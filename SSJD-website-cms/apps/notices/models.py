from django.db import models
from django.utils import timezone

from core.models import BaseModel
from core.validators import validate_document, validate_image


class Notice(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    description = models.TextField(blank=True)
    attachment_pdf = models.FileField(
        upload_to="notices/pdf/", blank=True, null=True, validators=[validate_document])
    thumbnail = models.ImageField(
        upload_to="notices/thumb/", blank=True, null=True, validators=[validate_image])
    publish_date = models.DateField(default=timezone.now, db_index=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    is_important = models.BooleanField(default=False, db_index=True, help_text="Pin to top")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-is_important", "-publish_date"]
        indexes = [models.Index(fields=["is_active", "publish_date"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.title)[:260] or "notice"
            slug, n = base, 1
            while Notice.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < timezone.now().date())
