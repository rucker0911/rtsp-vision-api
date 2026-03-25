import os
import socket

from django.db import connection, OperationalError
from rest_framework import status
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


class HealthView(APIView):
    permission_classes = [AllowAny]

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
