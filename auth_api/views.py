from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.logManager import LogManager
from utils.responses import (
    MISSING_PARAMETERS_422,
    SUCCESS_200,
    UNAUTHORIZED_401,
    response_with,
)

log = LogManager("auth_api")


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="登入取得 Token",
        description="以帳號密碼換取 API Token，後續請求帶入 `Authorization: Token <token>` header。",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["username", "password"],
            }
        },
        responses={200: None, 401: None, 422: None},
        examples=[
            OpenApiExample(
                "成功",
                value={"code": "success", "token": "9944b09199..."},
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return response_with(MISSING_PARAMETERS_422, error="username and password are required")

        user = authenticate(username=username, password=password)
        if not user:
            log.warning(f"Login failed for user: {username}")
            return response_with(UNAUTHORIZED_401)

        token, _ = Token.objects.get_or_create(user=user)
        log.info(f"Login success: {username}")
        return response_with(SUCCESS_200, value={"token": token.key})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="登出（刪除 Token）",
        description="刪除目前使用者的 API Token，需帶入有效的 `Authorization: Token <token>` header。",
        responses={200: None, 401: None},
    )
    def post(self, request: Request) -> Response:
        request.user.auth_token.delete()
        log.info(f"Logout success: {request.user.username}")
        return response_with(SUCCESS_200)
