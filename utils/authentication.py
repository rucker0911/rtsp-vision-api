from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

_EXPIRY_HOURS = getattr(settings, "TOKEN_EXPIRY_HOURS", 24)


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    在 DRF TokenAuthentication 基礎上加入有效期檢查。
    Token 超過 TOKEN_EXPIRY_HOURS 小時後自動刪除並回傳 401。
    """

    def authenticate_credentials(self, key: str):
        user, token = super().authenticate_credentials(key)

        expiry = token.created + timedelta(hours=_EXPIRY_HOURS)
        if timezone.now() > expiry:
            token.delete()
            raise AuthenticationFailed("Token has expired.")

        return user, token
