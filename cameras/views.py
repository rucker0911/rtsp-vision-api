from django.http import JsonResponse

from .models import CameraSource


def list_cameras(request):
    """
    簡單 API：回傳目前啟用的攝影機列表。
    之後可擴充為正式的 REST API。
    """
    cameras = CameraSource.objects.filter(is_enabled=True).order_by("name")
    data = [
        {
            "id": cam.id,
            "device_id": cam.device_id,
            "name": cam.name,
            "stream_url": cam.stream_url,
            "web_port": cam.web_port,
            "rtsp_port": cam.rtsp_port,
            "is_enabled": cam.is_enabled,
            # 不回傳 cctv_user / cctv_pass，避免外洩憑證
        }
        for cam in cameras
    ]
    return JsonResponse(
        {
            "code": "success",
            "data": data,
        }
    )