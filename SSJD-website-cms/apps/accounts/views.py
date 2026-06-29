from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import EmailToken
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    EmailVerifySerializer,
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from apps.accounts.tasks import send_email_task
from core.permissions import IsAdminOrReadOnly

User = get_user_model()


class LoginView(TokenObtainPairView):
    """JWT login — returns access + refresh tokens and the user profile."""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "login"


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutView(APIView):
    """Blacklist the supplied refresh token."""
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except Exception:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Logged out"}, status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(request=ChangePasswordSerializer, responses={200: None})
    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if not request.user.check_password(s.validated_data["old_password"]):
            return Response({"detail": "Old password is incorrect"}, status=400)
        request.user.set_password(s.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Password changed"})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = User.objects.filter(email=s.validated_data["email"]).first()
        if user:
            tok = EmailToken.objects.create(
                user=user, purpose=EmailToken.Purpose.RESET_PASSWORD,
                expires_at=timezone.now() + timedelta(hours=1))
            send_email_task.delay(
                "Reset your SSJD password",
                f"Use this token to reset your password: {tok.token}",
                user.email)
        # Always 200 — don't leak which emails exist.
        return Response({"detail": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tok = EmailToken.objects.filter(
            token=s.validated_data["token"],
            purpose=EmailToken.Purpose.RESET_PASSWORD).first()
        if not tok or not tok.is_valid:
            return Response({"detail": "Invalid or expired token"}, status=400)
        tok.user.set_password(s.validated_data["new_password"])
        tok.user.save(update_fields=["password"])
        tok.consume()
        return Response({"detail": "Password reset successful"})


class EmailVerifyView(APIView):
    permission_classes = [AllowAny]
    serializer_class = EmailVerifySerializer

    @extend_schema(request=EmailVerifySerializer, responses={200: None})
    def post(self, request):
        s = EmailVerifySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tok = EmailToken.objects.filter(
            token=s.validated_data["token"],
            purpose=EmailToken.Purpose.VERIFY_EMAIL).first()
        if not tok or not tok.is_valid:
            return Response({"detail": "Invalid or expired token"}, status=400)
        tok.user.email_verified = True
        tok.user.save(update_fields=["email_verified"])
        tok.consume()
        return Response({"detail": "Email verified"})


class UserViewSet(viewsets.ModelViewSet):
    """User management — Admin / Super Admin only for writes."""
    queryset = User.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "full_name", "phone"]
    ordering_fields = ["created_at", "full_name"]

    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer
