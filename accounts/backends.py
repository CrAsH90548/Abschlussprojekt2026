# ******************************************************************************
# * DJANGO CUSTOM AUTHENTICATION BACKEND                                       *
# * Dieses Modul ermöglicht den Login sowohl mit Benutzernamen als auch mit    *
# * E-Mail-Adresse, indem es die Standard-Authentifizierung erweitert.         *
# ******************************************************************************

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

# Wir holen uns das aktuell aktive User-Modell des Projekts.
# Das ist besser als 'from django.contrib.auth.models import User', da es
# auch funktioniert, wenn du ein eigenes (Custom) User-Modell verwendest.
UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Dieses Backend prüft, ob die Eingabe wie eine E-Mail aussieht (@-Zeichen).
    Wenn ja, sucht es nach der E-Mail, sonst nach dem Benutzernamen.
    """

    # **************************************************************************
    # * AUTHENTICATE METHODE                                                   *
    # * Dies ist der Einstiegspunkt, den Django aufruft, wenn du               *
    # * `authenticate()` in deinen Views benutzt.                              *
    # **************************************************************************
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Fallback: Manchmal wird der Benutzername nicht als 'username' Argument
        # übergeben, sondern steckt in den Keyword-Arguments (kwargs).
        # Wir versuchen, ihn dort zu finden, falls er oben 'None' ist.
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        # Lokale Variable für den gefundenen User initialisieren
        user = None

        # **********************************************************************
        # * LOGIK: E-MAIL ODER BENUTZERNAME?                                   *
        # * Wir nutzen eine einfache Heuristik: Enthält der String ein "@"?    *
        # **********************************************************************
        if username and "@" in username:
            # --- ZWEIG 1: E-MAIL LOGIN ---
            try:
                # Wir suchen den User anhand der E-Mail.
                # 'email__iexact' bedeutet: Case-Insensitive (Groß-/Kleinschreibung egal).
                # Das ist wichtig, da 'User@Example.com' und 'user@example.com' gleich sind.
                user = UserModel.objects.get(email__iexact=username)
            except UserModel.DoesNotExist:
                # Keine passende E-Mail in der Datenbank gefunden -> Authentifizierung fehlgeschlagen.
                return None
        else:
            # --- ZWEIG 2: BENUTZERNAME LOGIN ---
            try:
                # Hier suchen wir klassisch nach dem Feld, das als USERNAME_FIELD definiert ist.
                # Wir nutzen hier Dictionary-Unpacking (**{...}), um den Feldnamen dynamisch
                # zu setzen (falls dein User-Modell z.B. 'identifier' statt 'username' nutzt).
                user = UserModel.objects.get(**{UserModel.USERNAME_FIELD: username})
            except UserModel.DoesNotExist:
                # Kein passender Benutzername gefunden.
                return None

        # **********************************************************************
        # * PASSWORT UND STATUS PRÜFEN                                         *
        # * Nur wenn ein User gefunden wurde (user ist nicht None), prüfen wir:*
        # * 1. Stimmt das Passwort? (check_password hasht es und vergleicht)   *
        # * 2. Darf der User rein? (user_can_authenticate prüft z.B. is_active)*
        # **********************************************************************
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
            
        # Wenn Passwort falsch oder User inaktiv -> Fehlgeschlagen.
        return None