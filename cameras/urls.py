from django.urls import path

from .views import CameraCreateView, CameraDetailView, CameraListView

urlpatterns = [
    path("", CameraListView.as_view(), name="api-cameras-list"),
    path("create/", CameraCreateView.as_view(), name="api-cameras-create"),
    path("<str:device_id>/", CameraDetailView.as_view(), name="api-cameras-detail"),
]
