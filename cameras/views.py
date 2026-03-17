from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.responses import INVALID_INPUT_422, MISSING_PARAMETERS_422, SUCCESS_200, response_with

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
        summary="建立攝影機靜態資料",
        description="建立一筆新的攝影機設定。device_id 必須唯一，web_port / rtsp_port 範圍為 1–65535。",
        request=CameraCreateSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        serializer = CameraCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return response_with(MISSING_PARAMETERS_422, error=serializer.errors)

        if CameraSource.objects.filter(device_id=serializer.validated_data["device_id"]).exists():
            return response_with(INVALID_INPUT_422, error="device_id already exists")

        serializer.save()
        return response_with(SUCCESS_200)