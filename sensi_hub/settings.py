"""
Django settings for sensi_hub project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# Sicherheit / Debug
# ------------------------------------------------------------------------------
SECRET_KEY = 'django-insecure-$84xmi&kpx0ne(uka0rl3(1&!ku2)!)jqt#91(679aizi+&&h_'

DEBUG = True  # nur für Entwicklung!

# Erlaubte Hosts (LAN + lokal)
ALLOWED_HOSTS = [
    "192.168.178.170",
    "localhost",
    "127.0.0.1",
    "192.168.178.34",
    "100.67.137.21",
    "tail1697b2.ts.net",
]

# CSRF-Trusted für API-Aufrufe
CSRF_TRUSTED_ORIGINS = [
    "http://192.168.178.170:8000",
    "http://100.67.137.21:8000",
    "http://192.168.178.34:8000",
    "http://tail1697b2.ts.net:8000",
]

# ------------------------------------------------------------------------------
# Anwendungen
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "telemetry",
    "corsheaders",  # <--- hinzugefügt
    "accounts",     # <--- unsere neue App für Login/Registrierung
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # <--- möglichst weit oben
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sensi_hub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
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

# ------------------------------------------------------------------------------
# Datenbank
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

INGEST_TOKEN = "MY_DEV_TOKEN"

# ------------------------------------------------------------------------------
# Auth / Sprache / Zeitzone
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = False

# ------------------------------------------------------------------------------
# CORS-Konfiguration
# ------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",       # VS Code / http.server
    "http://127.0.0.1:5500",       # manchmal 127.0.0.1 statt localhost
    "http://192.168.178.170:5500", # falls du das Frontend aus dem LAN aufrufst
]

# Für Debugging (nicht in Produktion verwenden!)
# CORS_ALLOW_ALL_ORIGINS = False

# ------------------------------------------------------------------------------
# Statische Dateien
# ------------------------------------------------------------------------------
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# Accounts / Login / Auth-Backends
# ------------------------------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "frontend"        # nach Login auf Dashboard (/)
LOGOUT_REDIRECT_URL = "accounts:login" # nach Logout zurück auf Loginseite

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailOrUsernameBackend",  # E-Mail-Login (oder Username)
    "django.contrib.auth.backends.ModelBackend", # Standard
]

# ------------------------------------------------------------------------------
# E-Mail Versand (web.de SMTP)
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.web.de"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "smarthomedjango@web.de"
EMAIL_HOST_PASSWORD = "Techniker2026%!"

DEFAULT_FROM_EMAIL = "Sensor-Dashboard <smarthomedjango@web.de>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# Optional: „Eingeloggt bleiben“ für 30 Tage
# SESSION_COOKIE_AGE = 60*60*24*30
# SESSION_EXPIRE_AT_BROWSER_CLOSE = False
