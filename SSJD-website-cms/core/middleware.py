"""Thread-local current-user tracking for automatic audit stamping.

`BaseModel.save()` reads `get_current_user()` to populate created_by / updated_by
without every view having to pass `request.user` down to the model layer.
"""
import threading

_state = threading.local()


def get_current_user():
    return getattr(_state, "user", None)


def set_current_user(user):
    _state.user = user


class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        set_current_user(user if (user and user.is_authenticated) else None)
        try:
            return self.get_response(request)
        finally:
            set_current_user(None)
