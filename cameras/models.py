from django.db import models


class CameraSource(models.Model):
    """
    儲存攝影機來源設定，例如 RTSP URL。
    """

    device_id = models.CharField(max_length=100, unique=True, help_text="設備編號")
    name = models.CharField(max_length=100, db_index=True, help_text="攝影機顯示名稱")
    stream_url = models.CharField(max_length=500, help_text="串流 URL（例如 RTSP）")
    web_port = models.IntegerField(help_text="Web 存取埠號")
    rtsp_port = models.IntegerField(help_text="RTSP 埠號")
    cctv_user = models.CharField(max_length=100, blank=True, default="", help_text="CCTV 登入帳號")
    cctv_pass = models.CharField(max_length=100, blank=True, default="", help_text="CCTV 登入密碼")
    is_enabled = models.BooleanField(default=True, help_text="是否啟用此攝影機")
    is_online = models.BooleanField(default=False, help_text="最近一次連線檢查是否在線")
    last_checked_at = models.DateTimeField(null=True, blank=True, help_text="最近一次連線檢查時間")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Camera Source"
        verbose_name_plural = "Camera Sources"

    def __str__(self) -> str:
        return f"{self.device_id} - {self.name}"


class CameraStatusLog(models.Model):
    """
    記錄攝影機連線狀態變化事件，僅在 is_online 改變時寫入。
    """

    camera = models.ForeignKey(
        CameraSource,
        on_delete=models.CASCADE,
        related_name="status_logs",
        help_text="所屬攝影機",
    )
    is_online = models.BooleanField(help_text="變化後的連線狀態")
    changed_at = models.DateTimeField(help_text="狀態變化時間")

    class Meta:
        verbose_name = "Camera Status Log"
        verbose_name_plural = "Camera Status Logs"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["camera", "-changed_at"]),
        ]

    def __str__(self) -> str:
        state = "online" if self.is_online else "offline"
        return f"{self.camera.device_id} → {state} at {self.changed_at}"