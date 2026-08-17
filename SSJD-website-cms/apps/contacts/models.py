from django.db import models

from core.models import BaseModel


class InquiryType(models.TextChoices):
    GENERAL = "general", "General"
    ACCOUNT = "account", "Account / Savings"
    DEPOSIT = "deposit", "FD / RD"
    LOAN = "loan", "Loan"
    COMPLAINT = "complaint", "Complaint"
    OTHER = "other", "Other"


class LeadStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CLOSED = "closed", "Closed"


class Contact(BaseModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    message = models.TextField()
    inquiry_type = models.CharField(
        max_length=20, choices=InquiryType.choices, default=InquiryType.GENERAL, db_index=True)
    status = models.CharField(
        max_length=20, choices=LeadStatus.choices, default=LeadStatus.NEW, db_index=True)
    source = models.CharField(max_length=80, default="website")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact / Lead"

    def __str__(self):
        return f"{self.name} — {self.get_inquiry_type_display()}"
