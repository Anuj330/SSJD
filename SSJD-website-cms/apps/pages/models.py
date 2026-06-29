from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils.text import slugify

from core.models import BaseModel
from core.validators import validate_image


class Page(BaseModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = RichTextUploadingField(blank=True)
    featured_image = models.ImageField(
        upload_to="pages/", blank=True, null=True, validators=[validate_image])
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    is_published = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "page"
            slug, n = base, 1
            while Page.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
