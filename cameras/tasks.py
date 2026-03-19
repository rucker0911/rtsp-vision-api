import socket
from celery import shared_task
from django.utils import timezone

from utils.logManager import LogManager

log = LogManager("cameras.tasks")

_TCP_TIMEOUT = 3


def _tcp_check(host: str, port: int) -> bool:
    """對指定 host:port 做 TCP 握手，回傳是否成功。"""
    try:
        with socket.create_connection((host, port), timeout=_TCP_TIMEOUT):
            return True
    except OSError:
        return False


def _parse_host_port(stream_url: str, rtsp_port: int) -> tuple[str, int]:
    """
    從 stream_url 解析 host；若 URL 包含 port 則優先使用，
    否則 fallback 至 model 的 rtsp_port。
    """
    url = stream_url
    for scheme in ("rtsp://", "http://", "https://"):
        if url.lower().startswith(scheme):
            url = url[len(scheme):]
            break

    host_part = url.split("/")[0]
    if ":" in host_part:
        host, port_str = host_part.rsplit(":", 1)
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
    from cameras.models import CameraSource  # 避免 circular import

    cameras = CameraSource.objects.filter(is_enabled=True).only(
        "id", "device_id", "stream_url", "rtsp_port", "is_online"
    )

    now = timezone.now()
    updated, online_count = 0, 0

    for cam in cameras:
        host, port = _parse_host_port(cam.stream_url, cam.rtsp_port)
        online = _tcp_check(host, port)

        if online != cam.is_online:
            log.info(
                f"Camera status changed: {cam.device_id} "
                f"{'offline→online' if online else 'online→offline'}"
            )

        cam.is_online = online
        cam.last_checked_at = now
        if online:
            online_count += 1
        updated += 1

    CameraSource.objects.bulk_update(cameras, ["is_online", "last_checked_at"])
    log.info(f"Camera status check done: total={updated}, online={online_count}")
    return {"total": updated, "online": online_count}
