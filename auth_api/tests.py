from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthApiTests(APITestCase):
    def setUp(self) -> None:
        self.login_url = reverse("api-auth-login")
        self.logout_url = reverse("api-auth-logout")
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body.get("code"), "success")
        self.assertIn("token", body)
        self.assertTrue(len(body["token"]) > 0)

    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("code"), "notAuthorized")

    def test_login_missing_fields(self):
        response = self.client.post(self.login_url, {"username": "testuser"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.json().get("code"), "missingParameter")

    def test_logout_success(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("code"), "success")
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_cameras_without_token(self):
        response = self.client.get(reverse("api-cameras-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cameras_with_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get(reverse("api-cameras-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_throttle_returns_429(self):
        """超過限流次數後應回傳 429。"""
        payload = {"username": "testuser", "password": "wrongpass"}

        with patch("utils.throttles.LoginRateThrottle.allow_request", return_value=False):
            with patch("utils.throttles.LoginRateThrottle.wait", return_value=30.0):
                response = self.client.post(self.login_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        body = response.json()
        self.assertEqual(body.get("code"), "throttled")
        self.assertIn("message", body)
