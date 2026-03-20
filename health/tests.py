from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    """Health check 端點不需要 Token。"""

    def setUp(self) -> None:
        self.url = reverse("health")

    def test_health_ok(self):
        with patch("health.views._check_db", return_value="ok"), \
             patch("health.views._check_broker", return_value="ok"):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["db"], "ok")
        self.assertEqual(body["broker"], "ok")

    def test_health_db_error(self):
        with patch("health.views._check_db", return_value="error"), \
             patch("health.views._check_broker", return_value="ok"):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        body = response.json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["db"], "error")

    def test_health_broker_error(self):
        with patch("health.views._check_db", return_value="ok"), \
             patch("health.views._check_broker", return_value="error"):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        body = response.json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["broker"], "error")

    def test_health_no_token_required(self):
        """確認不帶 Token 也能存取。"""
        with patch("health.views._check_db", return_value="ok"), \
             patch("health.views._check_broker", return_value="ok"):
            response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
