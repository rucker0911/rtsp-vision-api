from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.responses import MISSING_PARAMETERS_422, SUCCESS_200, SUCCESS_201, response_with

from .models import CameraSource
from .serializers import CameraCreateSerializer, CameraSourceSerializer


class CameraListView(APIView):
    @extend_schema(
        summary="取得啟用中的攝影機列表",
        description="回傳所有 is_enabled=True 的攝影機，依名稱排序。不包含 cctv_user / cctv_pass。",
        responses=CameraSourceSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        cameras = CameraSource.objects.filter(is_enabled=True).order_by("name")
        serializer = CameraSourceSerializer(cameras, many=True)
        return Response({"code": "success", "data": serializer.data})


class CameraCreateView(APIView):
    @extend_schema(
        summary="新增或更新攝影機靜態資料（Upsert）",
        description=(
            "以 device_id 為識別鍵進行 upsert：\n"
            "- device_id 不存在 → 新增，回傳 201\n"
            "- device_id 已存在 → 僅更新有傳入的欄位（partial update），回傳 200\n"
            "web_port / rtsp_port 範圍為 1–65535。"
        ),
        request=CameraCreateSerializer,
        responses={200: None, 201: None},
    )
    def post(self, request: Request) -> Response:
        device_id = request.data.get("device_id")
        instance = CameraSource.objects.filter(device_id=device_id).first()

        if instance:
            serializer = CameraCreateSerializer(instance, data=request.data, partial=True)
            if not serializer.is_valid():
                return response_with(MISSING_PARAMETERS_422, error=serializer.errors)
            serializer.save()
            return response_with(SUCCESS_200)

        serializer = CameraCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return response_with(MISSING_PARAMETERS_422, error=serializer.errors)
        serializer.save()
        return response_with(SUCCESS_201)