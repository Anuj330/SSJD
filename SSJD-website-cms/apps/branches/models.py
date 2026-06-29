from django.conf import settings
from django.db import models

from core.models import BaseModel
from core.validators import validate_map_iframe


class Branch(BaseModel):
    branch_name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    pincode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    google_map_iframe = models.TextField(
        blank=True, validators=[validate_map_iframe],
        help_text="Embed <iframe> from Google Maps (only Google Maps embeds allowed)")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    branch_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="managed_branches")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["state", "city", "branch_name"]
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.branch_name} — {self.city}"
