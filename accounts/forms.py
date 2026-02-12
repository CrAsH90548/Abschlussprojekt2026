###############################################################################
# IMPORT-BEREICH: Hier lade ich die notwendigen Werkzeuge von Django,         #
# um Formulare zu erstellen und mit dem Benutzermodell zu arbeiten.           #
###############################################################################
from django import forms                                    # Basis-Klasse für alle Formular-Funktionen
from django.contrib.auth.forms import AuthenticationForm    # Vorgefertigte Logik für den Benutzer-Login
from django.contrib.auth.models import User                 # Das Standard-Benutzermodell von Django

###############################################################################
# LOGIN-FORMULAR: Ich erweitere die Standard-Login-Logik, um das Aussehen      #
# der Eingabefelder (Labels und Platzhalter) anzupassen.                      #
###############################################################################
class LoginForm(AuthenticationForm):
    # Hier definiere ich das Eingabefeld für den Benutzernamen neu, 
    # damit es als "E-Mail" angezeigt wird und einen hilfreichen Platzhalter hat.
    username = forms.CharField(
        label="E-Mail",
        widget=forms.TextInput(attrs={"placeholder": "z. B. max@firma.de"}),
    )
    
    # Auch das Passwort-Feld passe ich an, damit die Punkte (Sicherheits-Widget) 
    # und ein dezenter Platzhalter erscheinen.
    password = forms.CharField(
        label="Passwort",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )

###############################################################################
# REGISTRIERUNGS-FORMULAR: Ein ModelForm, das direkt mit dem User-Model       #
# verknüpft ist, um neue Konten in der Datenbank zu erstellen.                #
###############################################################################
class RegisterForm(forms.ModelForm):
    # Ich füge manuell zwei Passwort-Felder hinzu, da diese nicht 
    # standardmäßig im ModelForm für User (aus Sicherheitsgründen) enthalten sind.
    password1 = forms.CharField(label="Passwort", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Passwort (Wiederholung)", widget=forms.PasswordInput)

    ###########################################################################
    # META-DATEN: Hier sage ich Django, welches Model als Basis dient und     #
    # welche Felder ich im Formular anzeigen möchte.                          #
    ###########################################################################
    class Meta:
        model = User                                        # Ich verknüpfe das Formular mit der User-Tabelle
        fields = ("username", "email")                      # Diese Felder sollen aus dem Model übernommen werden
        labels = {"username": "Benutzername", "email": "E-Mail"} # Ich übersetze die Feldnamen für die Ansicht
        
        # Mit Widgets gestalte ich die HTML-Eingabefelder (z.B. CSS-Klassen oder Platzhalter)
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "z. B. max"}),
            "email": forms.EmailInput(attrs={"placeholder": "z. B. max@firma.de"}),
        }

    ###########################################################################
    # VALIDIERUNG: In diesem Block prüfe ich, ob die eingegebenen Daten       #
    # logisch korrekt sind (z. B. ob Passwörter übereinstimmen).              #
    ###########################################################################
    def clean(self):
        # Zuerst rufe ich die Standard-Validierung von Django auf
        cleaned = super().clean()
        # Ich hole mir die beiden Passwörter aus den bereinigten Daten
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        
        # Wenn beide Felder ausgefüllt sind, aber nicht identisch sind, werfe ich einen Fehler
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwörter stimmen nicht überein.")
        return cleaned

    ###########################################################################
    # E-MAIL-PRÜFUNG: Hier stelle ich sicher, dass keine E-Mail-Adresse       #
    # doppelt in meiner Datenbank vorkommt.                                   #
    ###########################################################################
    def clean_email(self):
        # Ich wandle die E-Mail in Kleinbuchstaben um, um Duplikate sicher zu finden
        email = self.cleaned_data.get("email", "").strip().lower()
        
        # Ich schaue in der Datenbank nach, ob diese E-Mail bereits existiert (case-insensitive)
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Diese E-Mail wird bereits verwendet.")
        return email

    ###########################################################################
    # SPEICHERN: Hier überschreibe ich die save-Methode, um das Passwort      #
    # sicher (gehasht) in die Datenbank zu schreiben.                         #
    ###########################################################################
    def save(self, commit=True):
        # Ich erstelle das User-Objekt, speichere es aber noch nicht in der Datenbank (commit=False)
        user = super().save(commit=False)
        
        # WICHTIG: Ich nutze set_password, damit das Passwort verschlüsselt wird 
        # und nicht im Klartext in der Datenbank landet!
        user.set_password(self.cleaned_data["password1"])
        
        # Falls gewünscht (Standard), wird der User jetzt endgültig gespeichert
        if commit:
            user.save()
        return user