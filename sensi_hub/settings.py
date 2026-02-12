"""
Django settings für das sensi_hub Projekt.
Hier lege ich die globalen Regeln und Verbindungen fest.
"""

from pathlib import Path

# Ich bestimme den Pfad zum Hauptverzeichnis meines Projekts,
# damit ich Dateien (wie die Datenbank) relativ dazu finden kann.
BASE_DIR = Path(__file__).resolve().parent.parent

##################################################################################
# SICHERHEIT & DEBUGGING: Hier steuere ich den Entwicklungsmodus und den Schutz. #
##################################################################################
# WICHTIG: Diesen Schlüssel halte ich geheim, er sichert meine Sessions und Hashes.
SECRET_KEY = 'django-insecure-$84xmi&kpx0ne(uka0rl3(1&!ku2)!)jqt#91(679aizi+&&h_'

# Wenn DEBUG auf True steht, zeigt mir Django bei Fehlern detaillierte Berichte.
# Im Live-Betrieb (Produktion) muss das zwingend auf False stehen!
DEBUG = True 

# Hier liste ich alle Adressen auf, unter denen mein Server erreichbar sein darf.
# Das schützt vor Angriffen, bei denen jemand meinen Host-Header fälscht.
ALLOWED_HOSTS = [
    "192.168.178.170", "localhost", "127.0.0.1",
    "192.168.178.34", "100.67.137.21", "tail1697b2.ts.net",
]

# CSRF-Schutz: Ich vertraue diesen Quellen bei Formularen und API-Anfragen.
CSRF_TRUSTED_ORIGINS = [
    "http://192.168.178.170:8000", "http://100.67.137.21:8000",
    "http://192.168.178.34:8000", "http://tail1697b2.ts.net:8000",
]

###############################################################################
# ANWENDUNGEN & MIDDLEWARE: Die modularen Bausteine meines Projekts.          #
###############################################################################
INSTALLED_APPS = [
    "django.contrib.admin",        # Die praktische Admin-Oberfläche
    "django.contrib.auth",         # Das Benutzer-System
    "django.contrib.contenttypes", # Erlaubt Verknüpfungen zwischen verschiedenen Models
    "django.contrib.sessions",     # Speichert Daten über Besuche hinweg
    "django.contrib.messages",     # Mein System für Feedback-Nachrichten
    "django.contrib.staticfiles",  # Verwaltung von CSS, JS und Bildern
    "telemetry",                   # Meine eigene App für Sensordaten
    "corsheaders",                 # Erlaubt Anfragen von anderen Servern (z.B. Frontend)
    "accounts",                    # Meine neue App für Login und Registrierung
]

# Middleware sind "Türsteher", die jede Anfrage passieren muss.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",           # Ich prüfe CORS-Rechte ganz am Anfang
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",       # Schutz gegen gefälschte Anfragen
    "django.contrib.auth.middleware.AuthenticationMiddleware", # Verknüpft User mit Anfragen
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sensi_hub.urls" # Wo liegt meine Haupt-URL-Konfiguration?

# Hier konfiguriere ich die Template-Engine (HTML-Erstellung)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],                # Zusätzliche Ordner für HTML-Dateien
        "APP_DIRS": True,          # Django sucht automatisch in jedem App-Ordner nach /templates/
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sensi_hub.wsgi.application"

###############################################################################
# DATENBANK & SPEICHER: Wo meine Daten dauerhaft abgelegt werden.             #
###############################################################################
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3", # Ich nutze SQLite (eine Datei), ideal für Entwicklung
        "NAME": BASE_DIR / "db.sqlite3",        # Die Datei liegt direkt in meinem Projektverzeichnis
    }
}

INGEST_TOKEN = "MY_DEV_TOKEN" # Mein eigener Token für die Datenaufnahme (API)

###############################################################################
# INTERNATIONALISIERUNG: Sprache und Zeit korrekt einstellen.                 #
###############################################################################
# Passwort-Regeln: Django achtet darauf, dass Passwörter nicht zu einfach sind.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"            # Mein Projekt spricht Deutsch
TIME_ZONE = "Europe/Berlin"        # Ich verwende unsere lokale Zeitzone
USE_I18N = True                    # Internationalisierung aktivieren
USE_TZ = False                     # Ich speichere Zeiten lieber naiv (ohne UTC-Umrechnung)

###############################################################################
# CORS: Erlaubt meinem Frontend, auf die API zuzugreifen.                     #
###############################################################################
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",       # VS Code Live Server
    "http://127.0.0.1:5500",
    "http://192.168.178.170:5500", # Zugriff aus dem lokalen Netzwerk
]

STATIC_URL = "static/"             # Unter welcher URL sind CSS/Bilder erreichbar?
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField" # Standard-Typ für Datenbank-IDs

###############################################################################
# AUTH-SYSTEM: Verhalten bei Login und Logout.                                #
###############################################################################
LOGIN_URL = "accounts:login"             # Wohin schicke ich Gäste, die eine geschützte Seite aufrufen?
LOGIN_REDIRECT_URL = "frontend"          # Ziel nach dem erfolgreichen Anmelden
LOGOUT_REDIRECT_URL = "accounts:login"    # Ziel nach dem Abmelden

# Ich erlaube den Login sowohl mit Benutzernamen als auch mit der E-Mail-Adresse.
AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailOrUsernameBackend", # Mein spezielles Backend
    "django.contrib.auth.backends.ModelBackend", # Das Standard-Backend als Fallback
]

###############################################################################
# E-MAIL VERSAND: Damit mein Passwort-Reset auch wirklich ankommt.            #
###############################################################################
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend" # Versand via SMTP-Server

EMAIL_HOST = "smtp.web.de"         # Postausgangsserver von Web.de
EMAIL_PORT = 587                   # Standardport für TLS-Verschlüsselung
EMAIL_USE_TLS = True               # Ich aktiviere die Verschlüsselung

EMAIL_HOST_USER = "smarthomedjango@web.de"  # Mein E-Mail-Account
EMAIL_HOST_PASSWORD = "Techniker2026%!"     # Mein App-Passwort (Sicherheit!)

DEFAULT_FROM_EMAIL = "Sensor-Dashboard <smarthomedjango@web.de>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL