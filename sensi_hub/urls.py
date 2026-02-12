from django.contrib import admin
from django.urls import path, include

# login_required: Ein Decorator, der sicherstellt, dass nur eingeloggte User eine View sehen.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect

# Import der Frontend-View aus deiner Telemetry-App
from telemetry.views import frontend

# --- HILFSFUNKTION: Einfacher Logout (GET-Request) ---
# Hintergrund: Seit Django 5 ist der Logout standardmäßig nur noch per POST-Request (Formular) möglich.
# Diese kleine Funktion erlaubt es dir, wieder einen einfachen Link <a href="/logout/"> zu nutzen.
def custom_logout_view(request):
    # Führt den eigentlichen Django-Logout aus (löscht Session-Daten etc.)
    logout(request)
    
    # Nach dem Logout leiten wir den User zur Login-Seite weiter.
    # Wichtig: Falls du die URL in 'accounts/urls.py' änderst, musst du diesen Pfad hier anpassen.
    return redirect('/auth/login/') 

urlpatterns = [
    # 1. Der Admin-Bereich
    # Erreichbar unter dein-server.de/admin/
    path("admin/", admin.site.urls),

    # 2. Das Dashboard (Startseite)
    # Die leere Zeichenkette "" bedeutet: Das ist die Root-URL (dein-server.de).
    # 'login_required(frontend)' wickelt die View in eine Sicherheitsabfrage. 
    # Wer nicht eingeloggt ist, wird automatisch zum Login geschickt.
    path("", login_required(frontend), name="frontend"),

    # 3. Authentifizierungs-Routen
    # Hier binden wir die 'accounts/urls.py' ein, die wir vorhin bearbeitet haben.
    # Alles was mit /auth/ beginnt, wird dort behandelt (z.B. /auth/login/).
    path("auth/", include("accounts.urls", namespace="accounts")),

    # 4. Globaler Logout
    # Dieser Pfad fängt /logout/ ab und nutzt unsere obige Hilfsfunktion.
    # Das ist praktisch, damit man nicht zwingend /auth/logout/ tippen muss.
    path("logout/", custom_logout_view, name="logout"),

    # 5. Telemetry-Routen
    # Hier werden alle weiteren URLs der Telemetry-App eingebunden.
    # Achtung: Da hier "" als Pfad steht, werden die URLs der App direkt angehängt.
    # Django prüft die Routen von oben nach unten. Was hier steht, kommt also als Letztes dran.
    path("", include("telemetry.urls")),
]