from django.urls import path

from .views import CameraCreateView, CameraListView

urlpatterns = [
    path("", CameraListView.as_view(), name="api-cameras-list"),
    path("create/", CameraCreateView.as_view(), name="api-cameras-create"),
]
