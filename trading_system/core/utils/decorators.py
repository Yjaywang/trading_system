# decorators.py

from functools import wraps
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


def require_secret_token(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")
        if not token:
            return Response(
                {"error": "Token is missing"}, status=status.HTTP_401_UNAUTHORIZED
            )
        if token.split(" ")[1] != settings.TRADING_SECRET_TOKEN:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return view_func(request, *args, **kwargs)

    return _wrapped_view
