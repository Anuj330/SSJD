from django.db import models

from core.models import BaseModel
from core.validators import validate_image


class Banner(BaseModel):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="banners/", validators=[validate_image])
    mobile_image = models.ImageField(
        upload_to="banners/mobile/", blank=True, null=True, validators=[validate_image])
    button_text = models.CharField(max_length=60, blank=True)
    button_link = models.URLField(blank=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["display_order", "-created_at"]
        indexes = [models.Index(fields=["is_active", "display_order"])]

    def __str__(self):
        return self.title
