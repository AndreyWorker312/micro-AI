from django.urls import path

from . import views

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    path("transcribe/", views.transcribe, name="transcribe"),
    path("confirm/", views.confirm, name="confirm"),
]

