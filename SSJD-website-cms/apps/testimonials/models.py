from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel
from core.validators import validate_image


class Testimonial(BaseModel):
    customer_name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, blank=True)
    review = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    profile_image = models.ImageField(
        upload_to="testimonials/", blank=True, null=True, validators=[validate_image])
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return f"{self.customer_name} ({self.rating}★)"
