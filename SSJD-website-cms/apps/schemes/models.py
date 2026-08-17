from django.db import models

from core.models import BaseModel
from core.validators import validate_image


class SchemeType(models.TextChoices):
    FD = "fd", "Fixed Deposit"
    RD = "rd", "Recurring Deposit"
    SAVINGS = "savings", "Savings"
    LOAN = "loan", "Loan"


class Scheme(BaseModel):
    scheme_name = models.CharField(max_length=200)
    scheme_type = models.CharField(max_length=16, choices=SchemeType.choices, db_index=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual % rate")
    tenure = models.CharField(max_length=100, blank=True, help_text="e.g. '12–60 months'")
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    benefits = models.TextField(blank=True, help_text="One benefit per line")
    image = models.ImageField(upload_to="schemes/", blank=True, null=True, validators=[validate_image])
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-is_featured", "scheme_name"]
        indexes = [models.Index(fields=["scheme_type", "is_active"])]

    def __str__(self):
        return f"{self.scheme_name} ({self.get_scheme_type_display()})"

    @property
    def benefit_list(self):
        return [b.strip() for b in self.benefits.splitlines() if b.strip()]
