from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.logManager import LogManager
from utils.responses import MISSING_PARAMETERS_422, NOT_FOUND_404, SUCCESS_200, SUCCESS_201, response_with

from .models import CameraSource
from .serializers import CameraCreateSerializer, CameraSourceSerializer, CameraStatusSerializer

log = LogManager("cameras")


class CameraListView(APIView):
    @extend_schema(
        summary="取得啟用中的攝影機列表",
        description="回傳所有 is_enabled=True 的攝影機，依名稱排序。不包含 cctv_user / cctv_pass。",
        responses=CameraSourceSerializer(many=True),
    )
    def get(self, request: Request) -> Response:
        cameras = CameraSource.objects.filter(is_enabled=True).order_by("name")
        serializer = CameraSourceSerializer(cameras, many=True)
        log.info(f"Camera list fetched, count={len(serializer.data)}")
        return response_with(SUCCESS_200, value={"data": serializer.data})


class CameraCreateView(APIView):
    @extend_schema(
        summary="新增或更新攝影機靜態資料",
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
                log.warning(f"Camera update validation failed: {serializer.errors}")
                return response_with(MISSING_PARAMETERS_422, error=serializer.errors)
            serializer.save()
            log.info(f"Camera updated: {device_id}")
            return response_with(SUCCESS_200)

        serializer = CameraCreateSerializer(data=request.data)
        if not serializer.is_valid():
            log.warning(f"Camera create validation failed: {serializer.errors}")
            return response_with(MISSING_PARAMETERS_422, error=serializer.errors)
        serializer.save()
        log.info(f"Camera created: {device_id}")
        return response_with(SUCCESS_201)


class CameraStatusView(APIView):
    @extend_schema(
        summary="查詢攝影機連線狀態",
        description="回傳指定攝影機的 is_online 與 last_checked_at，由 Celery Beat 每分鐘更新。",
        responses={200: CameraStatusSerializer, 404: None},
    )
    def get(self, request: Request, device_id: str) -> Response:
        instance = CameraSource.objects.filter(device_id=device_id).first()
        if not instance:
            log.warning(f"Camera status not found: {device_id}")
            return response_with(NOT_FOUND_404)
        serializer = CameraStatusSerializer(instance)
        log.info(f"Camera status fetched: {device_id}, online={instance.is_online}")
        return response_with(SUCCESS_200, value={"data": serializer.data})


class CameraDetailView(APIView):
    def _get_instance(self, device_id: str):
        return CameraSource.objects.filter(device_id=device_id).first()

    @extend_schema(
        summary="取得單筆攝影機資料",
        description="依 device_id 查詢單筆攝影機設定。不包含 cctv_user / cctv_pass。",
        responses={200: CameraSourceSerializer, 404: None},
    )
    def get(self, request: Request, device_id: str) -> Response:
        instance = self._get_instance(device_id)
        if not instance:
            log.warning(f"Camera not found: {device_id}")
            return response_with(NOT_FOUND_404)
        serializer = CameraSourceSerializer(instance)
        log.info(f"Camera fetched: {device_id}")
        return response_with(SUCCESS_200, value={"data": serializer.data})

    @extend_schema(
        summary="停用攝影機",
        description="依 device_id 將攝影機設為停用（is_enabled=False），資料保留不刪除。",
        responses={200: None, 404: None},
    )
    def delete(self, request: Request, device_id: str) -> Response:
        instance = self._get_instance(device_id)
        if not instance:
            log.warning(f"Camera not found for disable: {device_id}")
            return response_with(NOT_FOUND_404)
        instance.is_enabled = False
        instance.save(update_fields=["is_enabled", "updated_at"])
        log.info(f"Camera disabled: {device_id}")
        return response_with(SUCCESS_200)