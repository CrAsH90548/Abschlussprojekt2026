from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from telemetry.views import frontend   # Dashboard-Ansicht

urlpatterns = [
    # Adminbereich
    path("admin/", admin.site.urls),

    # Auth-Routen (Login, Logout, Registrierung, Passwort-Reset)
    path("auth/", include("accounts.urls", namespace="accounts")),

    # Dashboard (Root, geschützt mit Login)
    path("", login_required(frontend), name="frontend"),

    # Alle weiteren Telemetry-Routen (z. B. /api/ingest/)
    path("", include("telemetry.urls")),
]
