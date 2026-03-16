from django.contrib import admin
from .models import CameraSource


@admin.register(CameraSource)
class CameraSourceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "is_enabled", "web_port", "rtsp_port")
    search_fields = ("device_id", "name")
    list_filter = ("is_enabled",)