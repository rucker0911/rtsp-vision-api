from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.logManager import LogManager
from utils.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, paginate, parse_page_params
from utils.responses import MISSING_PARAMETERS_422, NOT_FOUND_404, SUCCESS_200, SUCCESS_201, response_with
from utils.schema import EXAMPLE_200, EXAMPLE_201, EXAMPLE_401, EXAMPLE_404, EXAMPLE_422

from .models import CameraSource, CameraStatusLog
from .serializers import CameraCreateSerializer, CameraSourceSerializer, CameraStatusLogSerializer, CameraStatusSerializer

log = LogManager("cameras")


class CameraListView(APIView):
    @extend_schema(
        summary="取得啟用中的攝影機列表",
        description=(
            "回傳所有 is_enabled=True 的攝影機，依名稱排序。\n"
            "支援分頁（page / page_size）與篩選（name / is_online）。\n"
            "不包含 cctv_user / cctv_pass。"
        ),
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, description="頁碼（預設 1）"),
            OpenApiParameter("page_size", OpenApiTypes.INT, description=f"每頁筆數（預設 {DEFAULT_PAGE_SIZE}，最大 {MAX_PAGE_SIZE}）"),
            OpenApiParameter("name", OpenApiTypes.STR, description="名稱模糊搜尋"),
            OpenApiParameter("is_online", OpenApiTypes.BOOL, description="篩選連線狀態（true / false）"),
        ],
        responses={200: CameraSourceSerializer(many=True), 401: None},
        examples=[EXAMPLE_401],
    )
    def get(self, request: Request) -> Response:
        qs = CameraSource.objects.filter(is_enabled=True).order_by("name")

        name = request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)

        is_online = request.query_params.get("is_online")
        if is_online is not None:
            qs = qs.filter(is_online=is_online.lower() == "true")

        page, page_size = parse_page_params(request.query_params)
        items, pagination = paginate(qs, page, page_size)
        serializer = CameraSourceSerializer(items, many=True)
        log.info(f"Camera list fetched, count={pagination['total']}, page={page}")
        return response_with(SUCCESS_200, value={"data": serializer.data}, pagination=pagination)


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
        responses={200: None, 201: None, 401: None, 422: None},
        examples=[EXAMPLE_200, EXAMPLE_201, EXAMPLE_401, EXAMPLE_422],
    )
    def post(self, request: Request) -> Response:
        device_id = request.data.get("device_id")
        if not device_id:
            return response_with(MISSING_PARAMETERS_422, error={"device_id": ["This field is required."]})

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
        responses={200: CameraStatusSerializer, 401: None, 404: None},
        examples=[EXAMPLE_401, EXAMPLE_404],
    )
    def get(self, request: Request, device_id: str) -> Response:
        instance = CameraSource.objects.filter(device_id=device_id).first()
        if not instance:
            log.warning(f"Camera status not found: {device_id}")
            return response_with(NOT_FOUND_404)
        serializer = CameraStatusSerializer(instance)
        log.info(f"Camera status fetched: {device_id}, online={instance.is_online}")
        return response_with(SUCCESS_200, value={"data": serializer.data})


class CameraHistoryView(APIView):
    @extend_schema(
        summary="查詢攝影機連線狀態歷史",
        description=(
            "回傳指定攝影機的連線狀態變化事件（僅記錄狀態改變的時間點）。\n"
            "支援時間範圍篩選（from_date / to_date，格式 YYYY-MM-DD）與分頁。"
        ),
        parameters=[
            OpenApiParameter("from_date", OpenApiTypes.DATE, description="開始日期（含）"),
            OpenApiParameter("to_date", OpenApiTypes.DATE, description="結束日期（含）"),
            OpenApiParameter("page", OpenApiTypes.INT, description="頁碼（預設 1）"),
            OpenApiParameter("page_size", OpenApiTypes.INT, description=f"每頁筆數（預設 {DEFAULT_PAGE_SIZE}，最大 {MAX_PAGE_SIZE}）"),
        ],
        responses={200: CameraStatusLogSerializer(many=True), 401: None, 404: None},
        examples=[EXAMPLE_401, EXAMPLE_404],
    )
    def get(self, request: Request, device_id: str) -> Response:
        camera = CameraSource.objects.filter(device_id=device_id).first()
        if not camera:
            log.warning(f"Camera history not found: {device_id}")
            return response_with(NOT_FOUND_404)

        qs = CameraStatusLog.objects.filter(camera=camera)

        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        if from_date:
            qs = qs.filter(changed_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(changed_at__date__lte=to_date)

        page, page_size = parse_page_params(request.query_params)
        items, pagination = paginate(qs, page, page_size)
        serializer = CameraStatusLogSerializer(items, many=True)

        online_count = qs.filter(is_online=True).count()
        total_events = pagination["total"]
        uptime_rate = round(online_count / total_events * 100, 1) if total_events else None

        log.info(f"Camera history fetched: {device_id}, events={total_events}")
        return response_with(
            SUCCESS_200,
            value={"data": serializer.data, "uptime_rate": uptime_rate},
            pagination=pagination,
        )


class CameraDetailView(APIView):
    def _get_instance(self, device_id: str):
        return CameraSource.objects.filter(device_id=device_id).first()

    @extend_schema(
        summary="取得單筆攝影機資料",
        description="依 device_id 查詢單筆攝影機設定。不包含 cctv_user / cctv_pass。",
        responses={200: CameraSourceSerializer, 401: None, 404: None},
        examples=[EXAMPLE_401, EXAMPLE_404],
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
        responses={200: None, 401: None, 404: None},
        examples=[EXAMPLE_200, EXAMPLE_401, EXAMPLE_404],
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