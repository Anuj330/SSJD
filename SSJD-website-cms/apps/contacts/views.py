import csv

from django.http import HttpResponse


def _csv_safe(value):
    """Neutralise CSV/formula injection — prefix cells that a spreadsheet
    would interpret as a formula (=, +, -, @, tab, CR) with a quote."""
    s = "" if value is None else str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from apps.contacts.models import Contact
from apps.contacts.serializers import ContactCreateSerializer, ContactSerializer
from apps.contacts.tasks import notify_new_lead


class ContactViewSet(viewsets.ModelViewSet):
    """Contact / leads.

    * Public (anonymous) may only **create** (submit the contact form), rate-limited.
    * Staff may list, filter, update status, and export leads to CSV.
    Lead data is never publicly readable.
    """
    queryset = Contact.objects.all()
    filterset_fields = ["inquiry_type", "status"]
    search_fields = ["name", "phone", "email", "message"]
    ordering_fields = ["created_at", "name"]

    def get_serializer_class(self):
        return ContactCreateSerializer if self.action == "create" else ContactSerializer

    def get_permissions(self):
        # Anyone may submit the form; everything else is staff-only.
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "contact"
        return super().get_throttles()

    def perform_create(self, serializer):
        contact = serializer.save()
        notify_new_lead.delay(str(contact.id))

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """Export the (filtered) leads as CSV — CRM-ready."""
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leads.csv"'
        writer = csv.writer(response)
        writer.writerow(["Name", "Phone", "Email", "Inquiry Type", "Status", "Message", "Created"])
        for c in qs:
            writer.writerow([_csv_safe(v) for v in (
                c.name, c.phone, c.email, c.get_inquiry_type_display(),
                c.get_status_display(), c.message, c.created_at.isoformat())])
        return response
