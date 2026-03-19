from django.db import models


class CameraSource(models.Model):
    """
    儲存攝影機來源設定，例如 RTSP URL。
    """

    device_id = models.CharField(max_length=100, unique=True, help_text="設備編號")
    name = models.CharField(max_length=100, help_text="攝影機顯示名稱")
    stream_url = models.CharField(max_length=500, help_text="串流 URL（例如 RTSP）")
    web_port = models.IntegerField(help_text="Web 存取埠號")
    rtsp_port = models.IntegerField(help_text="RTSP 埠號")
    cctv_user = models.CharField(max_length=100, help_text="CCTV 登入帳號")
    cctv_pass = models.CharField(default="temp_pass", max_length=100, help_text="CCTV 登入密碼")
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