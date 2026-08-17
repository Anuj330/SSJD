"""Shared rate limiter (slowapi). Keyed by client IP.

Used to throttle abuse-prone endpoints such as login. Register the limiter,
its state, and exception handler on the app in main.py.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
