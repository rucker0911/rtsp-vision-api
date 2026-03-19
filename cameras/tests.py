from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import CameraSource

VALID_PAYLOAD = {
    "device_id": "CAM001",
    "name": "Front Door",
    "stream_url": "rtsp://example.com/stream1",
    "web_port": 8080,
    "rtsp_port": 554,
    "cctv_user": "user1",
    "cctv_pass": "pass1",
}


class AuthMixin:
    """為 APITestCase 子類提供 Token 認證的共用 setUp 邏輯。"""

    def _set_auth(self) -> None:
        user = User.objects.create_user(username="testuser", password="testpass123")
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


class CameraListApiTests(AuthMixin, APITestCase):
    def setUp(self) -> None:
        self._set_auth()
        self.url = reverse("api-cameras-list")

    def test_list_cameras_only_enabled_returned(self):
        CameraSource.objects.create(
            device_id="CAM001",
            name="Front Door",
            stream_url="rtsp://example.com/stream1",
            web_port=8080,
            rtsp_port=554,
            cctv_user="user1",
            cctv_pass="pass1",
            is_enabled=True,
        )
        CameraSource.objects.create(
            device_id="CAM002",
            name="Back Door",
            stream_url="rtsp://example.com/stream2",
            web_port=8081,
            rtsp_port=554,
            cctv_user="user2",
            cctv_pass="pass2",
            is_enabled=False,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body.get("code"), "success")
        data = body.get("data", [])

        self.assertEqual(len(data), 1)
        item = data[0]
        self.assertEqual(item["device_id"], "CAM001")
        self.assertEqual(item["name"], "Front Door")
        self.assertEqual(item["stream_url"], "rtsp://example.com/stream1")
        self.assertEqual(item["web_port"], 8080)
        self.assertEqual(item["rtsp_port"], 554)
        self.assertTrue(item["is_enabled"])

        self.assertNotIn("cctv_user", item)
        self.assertNotIn("cctv_pass", item)


class CameraCreateApiTests(AuthMixin, APITestCase):
    def setUp(self) -> None:
        self._set_auth()
        self.url = reverse("api-cameras-create")

    def test_create_camera_success(self):
        response = self.client.post(self.url, VALID_PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertEqual(body.get("code"), "success")
        self.assertTrue(CameraSource.objects.filter(device_id="CAM001").exists())

    def test_create_camera_invalid_port(self):
        payload = {**VALID_PAYLOAD, "device_id": "CAM003", "web_port": 99999}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = response.json()
        self.assertEqual(body.get("code"), "missingParameter")
        self.assertIn("web_port", body.get("errors", {}))

    def test_update_camera_partial(self):
        CameraSource.objects.create(**VALID_PAYLOAD)

        updated_url = "rtsp://example.com/new-stream"
        response = self.client.post(
            self.url,
            {"device_id": "CAM001", "stream_url": updated_url},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body.get("code"), "success")
        self.assertEqual(
            CameraSource.objects.get(device_id="CAM001").stream_url,
            updated_url,
        )

    def test_update_camera_invalid_port(self):
        CameraSource.objects.create(**VALID_PAYLOAD)

        response = self.client.post(
            self.url,
            {"device_id": "CAM001", "rtsp_port": 99999},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = response.json()
        self.assertEqual(body.get("code"), "missingParameter")
        self.assertIn("rtsp_port", body.get("errors", {}))


class CameraDetailApiTests(AuthMixin, APITestCase):
    def setUp(self) -> None:
        self._set_auth()
        self.camera = CameraSource.objects.create(**VALID_PAYLOAD)
        self.url = reverse("api-cameras-detail", kwargs={"device_id": "CAM001"})
        self.not_found_url = reverse("api-cameras-detail", kwargs={"device_id": "NOTEXIST"})

    def test_get_camera_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body.get("code"), "success")
        item = body.get("data", {})
        self.assertEqual(item["device_id"], "CAM001")
        self.assertEqual(item["name"], "Front Door")
        self.assertNotIn("cctv_user", item)
        self.assertNotIn("cctv_pass", item)

    def test_get_camera_not_found(self):
        response = self.client.get(self.not_found_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get("code"), "notFound")

    def test_delete_camera_success(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("code"), "success")
        self.assertFalse(CameraSource.objects.get(device_id="CAM001").is_enabled)

    def test_delete_camera_not_found(self):
        response = self.client.delete(self.not_found_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get("code"), "notFound")
