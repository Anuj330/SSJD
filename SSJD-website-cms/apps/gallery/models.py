from django.db import models

from core.models import BaseModel
from core.validators import validate_image


class GalleryAlbum(BaseModel):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, db_index=True,
                                help_text="e.g. Events, Awards, Branches")
    event_date = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(
        upload_to="gallery/covers/", blank=True, null=True, validators=[validate_image])
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-event_date", "-created_at"]

    def __str__(self):
        return self.title


class GalleryImage(BaseModel):
    album = models.ForeignKey(GalleryAlbum, on_delete=models.CASCADE, related_name="images")
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="gallery/", validators=[validate_image])
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.title or f"Image {self.pk}"
