################################################################################
# IMPORT-BEREICH: Hier lade ich die Routing-Werkzeuge von Django und verknüpfe #
# die Logik (Views) mit den passenden Internetadressen (URLs).                 #
################################################################################
from django.urls import path                                # Importiert die Funktion, um URL-Muster zu definieren

# Ich importiere die eingebauten Authentifizierungs-Views von Django unter einem Alias,
# damit es keine Namenskonflikte mit meinen eigenen Funktionen gibt.
from django.contrib.auth import views as auth_views

# Hier binde ich meine eigenen, speziell gestalteten Ansichten ein.
# 'register' und 'logout_view' sind Funktionen, die anderen sind Klassen-Views.
from .views import (
    StyledLoginView, 
    register, 
    logout_view, 
    StyledPasswordResetView, 
    StyledPasswordResetConfirmView
)

# Ich lege den Namespace fest. Damit kann ich im restlichen Projekt
# via 'accounts:login' auf diese URLs verlinken, was sehr wartungsfreundlich ist.
app_name = "accounts"



###############################################################################
# URL-PATTERNS: Hier erstelle ich die "Straßenkarte" meiner App. Jede URL     #
# führt den Nutzer zu einer bestimmten Funktion oder Seite.                   #
###############################################################################
urlpatterns = [
    # --- GRUNDLEGENDE AUTHENTIFIZIERUNG ---

    # Hier definiere ich den Einstiegspunkt für den Login.
    # Da StyledLoginView eine Klasse ist, rufe ich .as_view() auf, um sie nutzbar zu machen.
    path("login/", StyledLoginView.as_view(), name="login"),

    # Für den Logout nutze ich meine eigene Funktion, die die Session sauber beendet.
    path("logout/", logout_view, name="logout"),

    # Die Registrierung neuer Nutzer läuft über diese URL.
    path("register/", register, name="register"),


    # --- PASSWORT ZURÜCKSETZEN (FLOW) ---
    # Ich implementiere den kompletten 4-Stufen-Prozess von Django,
    # damit Nutzer sicher ihre Passwörter wiederherstellen können.

    # 1. Schritt: Das Formular, in dem ich meine E-Mail-Adresse für den Reset eintippe.
    path("password-reset/", 
         StyledPasswordResetView.as_view(), 
         name="password_reset"),

    # 2. Schritt: Die Bestätigungsseite, die mir sagt: "Schau in dein Postfach!"
    # Ich nutze Djangos Standard-Logik, weise ihr aber mein eigenes schickes Template zu.
    path("password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done"),

    # 3. Schritt: Der magische Link aus der E-Mail. 
    # 'uidb64' (User-ID) und 'token' (Sicherheitsschlüssel) sorgen dafür, 
    # dass nur die berechtigte Person das Passwort ändern kann.
    path("reset/<uidb64>/<token>/",
        StyledPasswordResetConfirmView.as_view(),
        name="password_reset_confirm"),

    # 4. Schritt: Das "Finale". Hier wird bestätigt, dass das neue Passwort aktiv ist.
    # Auch hier überschreibe ich das Template, damit das Design einheitlich bleibt.
    path("reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete"),
]