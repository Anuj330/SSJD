"""Notice maintenance tasks (run via Celery beat)."""
from celery import shared_task
from django.utils import timezone


@shared_task
def deactivate_expired_notices():
    from apps.notices.models import Notice
    today = timezone.now().date()
    n = Notice.objects.filter(is_active=True, expiry_date__lt=today).update(is_active=False)
    return f"Deactivated {n} expired notices"
