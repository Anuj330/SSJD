from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class _RoleGuardMixin:
    """Prevent privilege escalation: only superusers may grant the
    Super Admin role (which carries full control of users + content)."""

    def validate_role(self, value):
        from apps.accounts.models import Role
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        if value == Role.SUPER_ADMIN and not (actor and actor.is_superuser):
            raise serializers.ValidationError(
                "Only a Super Admin can assign the Super Admin role.")
        return value


class UserSerializer(_RoleGuardMixin, serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role", "role_display",
                  "is_active", "is_staff", "email_verified", "created_at")
        # is_superuser is intentionally NOT exposed — managed via Django admin only.
        read_only_fields = ("id", "is_staff", "email_verified", "created_at")


class MeSerializer(serializers.ModelSerializer):
    """Self-service profile — a user may edit ONLY their own name/phone,
    never their role, active state, or staff flags (anti-escalation)."""
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role", "role_display",
                  "is_active", "is_staff", "email_verified", "created_at")
        read_only_fields = ("id", "email", "role", "role_display", "is_active",
                            "is_staff", "email_verified", "created_at")


class UserCreateSerializer(_RoleGuardMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "role", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Adds user profile + role claims to the JWT and the login response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8)


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.UUIDField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
