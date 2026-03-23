from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import CameraSource, CameraStatusLog

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

    def _bulk_create(self, count: int):
        CameraSource.objects.bulk_create([
            CameraSource(
                device_id=f"CAM{i:03d}",
                name=f"Camera {i:03d}",
                stream_url=f"rtsp://example.com/stream{i}",
                web_port=8080 + i,
                rtsp_port=554,
                cctv_user="user",
                cctv_pass="pass",
                is_enabled=True,
                is_online=(i % 2 == 0),
            )
            for i in range(1, count + 1)
        ])

    def test_pagination_returns_correct_page(self):
        self._bulk_create(25)
        response = self.client.get(self.url, {"page": 2, "page_size": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body["data"]), 10)
        pagination = body["pagination"]
        self.assertEqual(pagination["page"], 2)
        self.assertEqual(pagination["total"], 25)
        self.assertEqual(pagination["total_pages"], 3)

    def test_filter_by_name(self):
        self._bulk_create(5)
        CameraSource.objects.create(
            device_id="SPECIAL",
            name="Lobby Entrance",
            stream_url="rtsp://example.com/lobby",
            web_port=9090,
            rtsp_port=554,
            cctv_user="u",
            cctv_pass="p",
            is_enabled=True,
        )
        response = self.client.get(self.url, {"name": "lobby"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["device_id"], "SPECIAL")

    def test_filter_by_is_online(self):
        self._bulk_create(6)
        response = self.client.get(self.url, {"is_online": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertTrue(all(item["is_online"] for item in body["data"]))

    def test_page_size_capped_at_max(self):
        self._bulk_create(10)
        response = self.client.get(self.url, {"page_size": 9999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(response.json()["pagination"]["page_size"], 100)


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

    def test_create_camera_missing_device_id(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "device_id"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        body = response.json()
        self.assertEqual(body.get("code"), "missingParameter")
        self.assertIn("device_id", body.get("errors", {}))

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


class CameraStatusApiTests(AuthMixin, APITestCase):
    def setUp(self) -> None:
        self._set_auth()
        self.camera = CameraSource.objects.create(
            **VALID_PAYLOAD,
            is_online=True,
            last_checked_at=timezone.now(),
        )
        self.url = reverse("api-cameras-status", kwargs={"device_id": "CAM001"})
        self.not_found_url = reverse("api-cameras-status", kwargs={"device_id": "NOTEXIST"})

    def test_status_online(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body.get("code"), "success")
        data = body.get("data", {})
        self.assertEqual(data["device_id"], "CAM001")
        self.assertTrue(data["is_online"])
        self.assertIsNotNone(data["last_checked_at"])

    def test_status_offline(self):
        self.camera.is_online = False
        self.camera.save(update_fields=["is_online"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["data"]["is_online"])

    def test_status_not_found(self):
        response = self.client.get(self.not_found_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get("code"), "notFound")


class CameraCheckTaskTests(APITestCase):
    """驗證 check_all_cameras_status task 正確更新 is_online。"""

    def test_task_marks_online(self):
        CameraSource.objects.create(
            **{**VALID_PAYLOAD, "stream_url": "rtsp://192.0.2.1/stream"},
        )
        from cameras.tasks import check_all_cameras_status

        with patch("cameras.tasks._tcp_check", return_value=True):
            result = check_all_cameras_status()

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["online"], 1)
        self.assertTrue(CameraSource.objects.get(device_id="CAM001").is_online)

    def test_task_marks_offline(self):
        CameraSource.objects.create(
            **{**VALID_PAYLOAD, "stream_url": "rtsp://192.0.2.1/stream"},
            is_online=True,
        )
        from cameras.tasks import check_all_cameras_status

        with patch("cameras.tasks._tcp_check", return_value=False):
            result = check_all_cameras_status()

        self.assertEqual(result["online"], 0)
        self.assertFalse(CameraSource.objects.get(device_id="CAM001").is_online)

    def test_task_writes_status_log_on_change(self):
        CameraSource.objects.create(
            **{**VALID_PAYLOAD, "stream_url": "rtsp://192.0.2.1/stream"},
            is_online=False,
        )
        from cameras.tasks import check_all_cameras_status

        with patch("cameras.tasks._tcp_check", return_value=True):
            check_all_cameras_status()

        self.assertEqual(CameraStatusLog.objects.count(), 1)
        log_entry = CameraStatusLog.objects.first()
        self.assertTrue(log_entry.is_online)

    def test_task_no_log_when_status_unchanged(self):
        CameraSource.objects.create(
            **{**VALID_PAYLOAD, "stream_url": "rtsp://192.0.2.1/stream"},
            is_online=True,
        )
        from cameras.tasks import check_all_cameras_status

        with patch("cameras.tasks._tcp_check", return_value=True):
            check_all_cameras_status()

        self.assertEqual(CameraStatusLog.objects.count(), 0)


class CameraHistoryApiTests(AuthMixin, APITestCase):
    def setUp(self) -> None:
        self._set_auth()
        self.camera = CameraSource.objects.create(**VALID_PAYLOAD)
        self.url = reverse("api-cameras-history", kwargs={"device_id": "CAM001"})
        self.not_found_url = reverse("api-cameras-history", kwargs={"device_id": "NOTEXIST"})

    def _create_logs(self, count: int):
        now = timezone.now()
        CameraStatusLog.objects.bulk_create([
            CameraStatusLog(
                camera=self.camera,
                is_online=(i % 2 == 0),
                changed_at=now,
            )
            for i in range(count)
        ])

    def test_history_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["pagination"]["total"], 0)
        self.assertEqual(body["data"], [])

    def test_history_returns_logs(self):
        self._create_logs(5)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["pagination"]["total"], 5)
        self.assertEqual(len(body["data"]), 5)
        self.assertIn("is_online", body["data"][0])
        self.assertIn("changed_at", body["data"][0])

    def test_history_not_found(self):
        response = self.client.get(self.not_found_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get("code"), "notFound")

    def test_history_uptime_rate(self):
        self._create_logs(4)
        response = self.client.get(self.url)
        body = response.json()
        self.assertIn("uptime_rate", body)
        self.assertIsNotNone(body["uptime_rate"])
