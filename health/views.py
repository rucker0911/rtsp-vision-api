import os
import socket

from django.db import connection, OperationalError
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


def _check_db() -> str:
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "ok"
    except OperationalError:
        return "error"


def _check_broker() -> str:
    """從 RABBITMQ_URL 解析 host:port 並做 TCP 連線測試"""
    try:
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
        # amqp://user:pass@host:port/vhost
        host_part = url.split("@")[-1].split("/")[0]
        if ":" in host_part:
            host, port_str = host_part.rsplit(":", 1)
            port = int(port_str)
        else:
            host, port = host_part, 5672
        with socket.create_connection((host, port), timeout=2):
            return "ok"
    except OSError:
        return "error"


class _HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    db = serializers.ChoiceField(choices=["ok", "error"])
    broker = serializers.ChoiceField(choices=["ok", "error"])


_EXAMPLE_HEALTH_OK = OpenApiExample(
    "全部正常",
    value={"status": "ok", "db": "ok", "broker": "ok"},
    response_only=True,
    status_codes=["200"],
)

_EXAMPLE_HEALTH_DEGRADED = OpenApiExample(
    "部分服務異常",
    value={"status": "degraded", "db": "ok", "broker": "error"},
    response_only=True,
    status_codes=["503"],
)


class HealthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="服務健康檢查",
        description="檢查 PostgreSQL 與 RabbitMQ 連線狀態。全部正常回傳 200，任一異常回傳 503。",
        responses={200: _HealthResponseSerializer, 503: _HealthResponseSerializer},
        examples=[_EXAMPLE_HEALTH_OK, _EXAMPLE_HEALTH_DEGRADED],
    )
    def get(self, request: Request) -> Response:
        db = _check_db()
        broker = _check_broker()
        all_ok = db == "ok" and broker == "ok"

        payload = {
            "status": "ok" if all_ok else "degraded",
            "db": db,
            "broker": broker,
        }
        http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=http_status)
