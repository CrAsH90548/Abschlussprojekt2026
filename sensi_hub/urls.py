from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from telemetry.views import frontend

# --- NEU: Eine kleine Hilfsfunktion für den Logout ---
# Diese Funktion erlaubt den Logout per einfachem Klick (GET-Request),
# was Django 5 standardmäßig sonst blockiert.
def custom_logout_view(request):
    logout(request)
    # Hier springen wir zurück zum Login. 
    # Falls dein Login woanders liegt, passe '/auth/login/' an.
    return redirect('/auth/login/') 

urlpatterns = [
    # Adminbereich
    path("admin/", admin.site.urls),

    # Dashboard (Root, geschützt mit Login)
    path("", login_required(frontend), name="frontend"),

    # Auth-Routen
    path("auth/", include("accounts.urls", namespace="accounts")),

    # --- HIER: Der Logout-Pfad nutzt jetzt unsere Hilfsfunktion ---
    path("logout/", custom_logout_view, name="logout"),

    # Alle weiteren Telemetry-Routen
    path("", include("telemetry.urls")),
]