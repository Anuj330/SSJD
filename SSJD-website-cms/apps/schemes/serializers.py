from rest_framework import serializers

from apps.schemes.models import Scheme


class SchemeSerializer(serializers.ModelSerializer):
    scheme_type_display = serializers.CharField(source="get_scheme_type_display", read_only=True)
    benefit_list = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Scheme
        fields = ("id", "scheme_name", "scheme_type", "scheme_type_display",
                  "interest_rate", "tenure", "minimum_amount", "description",
                  "benefits", "benefit_list", "image", "is_featured", "is_active",
                  "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
