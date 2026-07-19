from django.core.cache import cache
from django.db import models

from core.validators import validate_image

CACHE_KEY = "site_settings_singleton"


class SiteSetting(models.Model):
    """Singleton holding global website settings."""
    # Branding
    site_name = models.CharField(max_length=150, default="Shree Shyam Jan Kalyan Co-operative (U) Thrift & Credit Society Ltd.")
    logo = models.ImageField(upload_to="settings/", blank=True, null=True, validators=[validate_image])
    favicon = models.ImageField(upload_to="settings/", blank=True, null=True, validators=[validate_image])

    # Contact details
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_address = models.TextField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)

    # Social links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Footer
    footer_about = models.TextField(blank=True)
    footer_copyright = models.CharField(max_length=255, blank=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)

    # Analytics (raw script snippets injected by the frontend)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    head_scripts = models.TextField(blank=True)
    body_scripts = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Website Settings"
        verbose_name_plural = "Website Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)
        cache.delete(CACHE_KEY)

    @classmethod
    def load(cls):
        obj = cache.get(CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(CACHE_KEY, obj, 3600)
        return obj
