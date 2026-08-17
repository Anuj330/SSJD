from rest_framework import serializers

from apps.testimonials.models import Testimonial


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ("id", "customer_name", "designation", "review", "rating",
                  "profile_image", "display_order", "is_active",
                  "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
