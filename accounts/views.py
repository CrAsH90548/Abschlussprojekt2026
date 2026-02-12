###############################################################################
# IMPORT-BEREICH: Hier lade ich die Werkzeuge für Nachrichten, Authentifizierung #
# und die Navigation innerhalb meiner Anwendung.                              #
###############################################################################
from django.contrib import messages                         # Für kleine Pop-up-Benachrichtigungen (Erfolg/Fehler)
from django.contrib.auth import login, logout               # Kernfunktionen zum An- und Abmelden von Usern
from django.contrib.auth.views import (                     # Basis-Klassen für den Login und Passwort-Reset
    LoginView, 
    PasswordResetView, 
    PasswordResetConfirmView
)
from django.shortcuts import redirect, render              # Zum Weiterleiten oder Rendern von HTML-Seiten
from django.urls import reverse_lazy                        # Erstellt URLs erst dann, wenn sie wirklich gebraucht werden

from .forms import LoginForm, RegisterForm                  # Meine selbst erstellten Formular-Klassen

###############################################################################
# LOGIN-LOGIK: Ich nutze die LoginView von Django und passe sie an mein        #
# eigenes Design und meine Benachrichtigungen an.                             #
###############################################################################
class StyledLoginView(LoginView):
    template_name = "accounts/login.html"                   # Ich sage Django, welche HTML-Datei das Design liefert
    authentication_form = LoginForm                         # Ich verknüpfe mein speziell gestyltes Formular
    redirect_authenticated_user = True                      # Wer schon eingeloggt ist, wird direkt weitergeleitet

    def form_valid(self, form):
        # Wenn die Daten korrekt sind, schicke ich eine Erfolgsmeldung ab
        messages.success(self.request, "Willkommen zurück!")
        return super().form_valid(form)                     # Hier wird die eigentliche Anmeldung durchgeführt

###############################################################################
# REGISTRIERUNG: Eine Funktions-basierte View, um neue Nutzerkonten           #
# sicher anzulegen und sie sofort einzuloggen.                                #
###############################################################################
def register(request):
    # Falls der User bereits angemeldet ist, schicke ich ihn weg zur Startseite
    if request.user.is_authenticated:
        return redirect("frontend")
    
    # Wurde das Formular abgeschickt? (POST-Methode)
    if request.method == "POST":
        form = RegisterForm(request.POST)                   # Ich fülle das Formular mit den abgeschickten Daten
        if form.is_valid():                                 # Ich prüfe, ob alle Eingaben (z.B. Passwörter) korrekt sind
            user = form.save()                              # Ich erstelle den neuen User in der Datenbank
            login(request, user)                            # Ich logge den neuen User sofort automatisch ein
            messages.success(request, "Account erstellt. Viel Spaß!")
            return redirect("frontend")                     # Ab zur Startseite
    else:
        # Falls die Seite normal aufgerufen wird (GET), zeige ich ein leeres Formular
        form = RegisterForm()
    
    # Ich rendere die Seite und übergebe das Formular an das Template
    return render(request, "accounts/register.html", {"form": form})

###############################################################################
# LOGOUT: Eine einfache Funktion, um die aktuelle Sitzung zu beenden.         #
###############################################################################
def logout_view(request):
    logout(request)                                         # Ich lösche die Session-Daten des Nutzers
    messages.info(request, "Du wurdest abgemeldet.")        # Kurze Info über die Abmeldung
    return redirect("accounts:login")                       # Zurück zum Login-Bildschirm

###############################################################################
# PASSWORT-RESET: Diese Klassen steuern den Ablauf, wenn jemand sein          #
# Passwort vergessen hat.                                                     #
###############################################################################

# Schritt 1: E-Mail-Adresse abfragen
class StyledPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"          # Das Design für die E-Mail-Abfrage
    email_template_name = "accounts/password_reset_email.txt" # Der Textinhalt der Reset-E-Mail
    # Nach dem Abschicken leite ich zur "Erfolg"-Seite weiter
    success_url = reverse_lazy("accounts:password_reset_done")

# Schritt 2: Das Setzen des neuen Passworts über den E-Mail-Link
class StyledPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"  # Hier tippt der User sein neues Passwort ein
    # Wenn alles geklappt hat, geht es zur Abschlussseite
    success_url = reverse_lazy("accounts:password_reset_complete")