from django import forms
from django.contrib.auth.forms import (
    UserChangeForm as BaseUserChangeForm,
    UserCreationForm as BaseUserCreationForm,
)

from apps.accounts.models import User


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name", "role")


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
