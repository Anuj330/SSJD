from django.contrib import admin

from apps.testimonials.models import Testimonial
from core.admin import BaseModelAdmin


@admin.register(Testimonial)
class TestimonialAdmin(BaseModelAdmin):
    list_display = ("customer_name", "designation", "rating", "is_active", "display_order")
    list_editable = ("is_active", "display_order")
    list_filter = ("rating", "is_active")
    search_fields = ("customer_name", "review")
