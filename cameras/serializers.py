from rest_framework import serializers

from .models import CameraSource

PORT_MIN = 1
PORT_MAX = 65535


class CameraSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraSource
        fields = [
            "id",
            "device_id",
            "name",
            "stream_url",
            "web_port",
            "rtsp_port",
            "is_enabled",
            "is_online",
            "last_checked_at",
        ]


class CameraStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraSource
        fields = ["device_id", "name", "is_online", "last_checked_at"]


class CameraCreateSerializer(serializers.ModelSerializer):
    web_port = serializers.IntegerField(min_value=PORT_MIN, max_value=PORT_MAX)
    rtsp_port = serializers.IntegerField(min_value=PORT_MIN, max_value=PORT_MAX)

    class Meta:
        model = CameraSource
        fields = [
            "device_id",
            "name",
            "stream_url",
            "web_port",
            "rtsp_port",
            "cctv_user",
            "cctv_pass",
            "is_enabled",
        ]
        extra_kwargs = {
            "is_enabled": {"default": True},
        }
