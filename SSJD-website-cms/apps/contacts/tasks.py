"""Lead notification tasks."""
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def notify_new_lead(contact_id):
    from apps.contacts.models import Contact
    c = Contact.all_objects.filter(id=contact_id).first()
    if not c:
        return "Lead not found"
    body = (f"New website inquiry\n\n"
            f"Name: {c.name}\nPhone: {c.phone}\nEmail: {c.email}\n"
            f"Type: {c.get_inquiry_type_display()}\n\nMessage:\n{c.message}")
    send_mail("New website lead", body, settings.DEFAULT_FROM_EMAIL,
              [settings.LEAD_NOTIFY_EMAIL], fail_silently=True)
    return f"Notified for lead {contact_id}"
