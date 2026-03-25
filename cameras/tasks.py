import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from utils.logManager import LogManager

log = LogManager("cameras.tasks")

_TCP_TIMEOUT = 3
_MAX_WORKERS = 20


def _tcp_check(host: str, port: int) -> bool:
    """對指定 host:port 做 TCP 握手，回傳是否成功。"""
    try:
        with socket.create_connection((host, port), timeout=_TCP_TIMEOUT):
            return True
    except OSError:
        return False


def _parse_host_port(stream_url: str, rtsp_port: int) -> tuple[str, int] | None:
    """
    從 stream_url 解析 host；若 URL 包含 port 則優先使用，
    否則 fallback 至 model 的 rtsp_port。
    回傳 None 表示 URL 無效（空字串或解析不出 host）。
    """
    if not stream_url or not stream_url.strip():
        return None

    url = stream_url.strip()
    for scheme in ("rtsp://", "http://", "https://"):
        if url.lower().startswith(scheme):
            url = url[len(scheme):]
            break

    host_part = url.split("/")[0].strip()
    if not host_part:
        return None

    if ":" in host_part:
        host, port_str = host_part.rsplit(":", 1)
        host = host.strip()
        if not host:
            return None
        try:
            return host, int(port_str)
        except ValueError:
            pass
    return host_part, rtsp_port


@shared_task(name="cameras.check_all_cameras_status")
def check_all_cameras_status() -> dict:
    """
    每分鐘掃描所有啟用中的攝影機，對 stream_url 的 host+port 做 TCP 連線測試，
    並將結果寫回 is_online / last_checked_at。
    """
    from cameras.models import CameraSource, CameraStatusLog  # 避免 circular import

    cameras = list(
        CameraSource.objects.filter(is_enabled=True).only(
            "id", "device_id", "stream_url", "rtsp_port", "is_online"
        )
    )

    now = timezone.now()
    online_count = 0
    status_logs = []

    def _check(cam):
        result = _parse_host_port(cam.stream_url, cam.rtsp_port)
        if result is None:
            log.warning(f"Invalid stream_url for camera: {cam.device_id} ({cam.stream_url!r})")
            return cam, False
        host, port = result
        return cam, _tcp_check(host, port)

    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(cameras) or 1)) as executor:
        futures = {executor.submit(_check, cam): cam for cam in cameras}
        for future in as_completed(futures):
            cam, online = future.result()
            if online != cam.is_online:
                log.info(
                    f"Camera status changed: {cam.device_id} "
                    f"{'offline→online' if online else 'online→offline'}"
                )
                status_logs.append(
                    CameraStatusLog(camera_id=cam.id, is_online=online, changed_at=now)
                )
            cam.is_online = online
            cam.last_checked_at = now
            if online:
                online_count += 1

    updated = len(cameras)
    CameraSource.objects.bulk_update(cameras, ["is_online", "last_checked_at"])
    if status_logs:
        CameraStatusLog.objects.bulk_create(status_logs)
    log.info(f"Camera status check done: total={updated}, online={online_count}")
    return {"total": updated, "online": online_count}
