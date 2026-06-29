from rest_framework import serializers

from apps.branches.models import Branch


class BranchSerializer(serializers.ModelSerializer):
    branch_manager_name = serializers.CharField(source="branch_manager.full_name", read_only=True)

    class Meta:
        model = Branch
        fields = ("id", "branch_name", "address", "city", "state", "pincode",
                  "phone", "email", "google_map_iframe", "latitude", "longitude",
                  "branch_manager", "branch_manager_name", "is_active",
                  "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
