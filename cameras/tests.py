from django.test import TestCase
from django.urls import reverse

from .models import CameraSource


class CameraApiTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse("api-cameras-list")

    def test_list_cameras_only_enabled_returned(self):
        # 建立啟用的攝影機
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
        # 建立未啟用的攝影機
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
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body.get("code"), "success")
        data = body.get("data", [])

        # 只會回傳啟用的那一筆
        self.assertEqual(len(data), 1)
        item = data[0]
        self.assertEqual(item["device_id"], "CAM001")
        self.assertEqual(item["name"], "Front Door")
        self.assertEqual(item["stream_url"], "rtsp://example.com/stream1")
        self.assertEqual(item["web_port"], 8080)
        self.assertEqual(item["rtsp_port"], 554)
        self.assertTrue(item["is_enabled"])

        # 確認沒有敏感資訊
        self.assertNotIn("cctv_user", item)
        self.assertNotIn("cctv_pass", item)