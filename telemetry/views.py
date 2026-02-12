from __future__ import annotations

# Standard-Bibliotheken für JSON-Verarbeitung und Typ-Hinweise
import json
from typing import Optional

# Django-Kernfunktionen
from django.conf import settings                    # Um auf Einstellungen wie USE_TZ zuzugreifen
from django.db import transaction                   # Für atomare Datenbank-Operationen (alles oder nichts)
from django.db.models import Q                      # Ermöglicht komplexe Suchabfragen (ODER-Verknüpfungen)
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render                 # Zum Rendern von HTML-Templates
from django.utils import timezone                   # Djangos Werkzeug für Zeitzonen-Handling
from django.utils.dateparse import parse_datetime   # Hilft, Strings in echte Datumsobjekte zu wandeln
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie # Sicherheitseinstellungen für APIs

# Import meiner eigenen Datenbank-Modelle
from .models import SensorType, Sensor, Reading


###############################################################################
# HELPER-FUNKTIONEN
# Diese kleinen Helferlein halten den eigentlichen View-Code sauber und 
# kümmern sich um wiederkehrende Aufgaben wie Zeit-Konvertierung.
###############################################################################

def _to_local_iso(ts) -> str:
    """
    Wandelt einen Datenbank-Zeitstempel in einen ISO-String um.
    Der Clou: Er beachtet die 'TIME_ZONE'-Einstellung aus settings.py.
    """
    # Fall 1: Django arbeitet mit Zeitzonen (USE_TZ=True)
    if settings.USE_TZ:
        # Falls der Timestamp noch "naiv" (ohne Zeitzone) ist, mache ich ihn "aware"
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, timezone.get_current_timezone())
        # Ich rechne die Zeit in die lokale Zone (z.B. Berlin) um
        return timezone.localtime(ts, timezone.get_current_timezone()).isoformat()
    
    # Fall 2: Django arbeitet "naiv" (USE_TZ=False), ich gebe den Zeitstempel direkt zurück
    return ts.isoformat()


def _extract_values(data: dict):
    """
    Versucht, Temperatur, Feuchte und Wassertemperatur aus dem JSON-Datenpaket zu lesen.
    Da Sensoren oft unterschiedliche Keys senden (z.B. 'temp' vs 'temperature'),
    probiere ich hier verschiedene Varianten durch ('Robustness Principle').
    """
    if not isinstance(data, dict):
        return None, None, None

    # Ich suche nach Temperatur (Priorität: temperature_c -> temp_c -> temperature -> temp)
    temp = (
        data.get("temperature_c")
        or data.get("temp_c")
        or data.get("temperature")
        or data.get("temp")
    )
    # Dasselbe für die Luftfeuchtigkeit
    hum = (
        data.get("humidity_percent")
        or data.get("humidity")
        or data.get("hum")
    )
    # Und für die Wassertemperatur
    wtemp = (
        data.get("water_temperature_c")
        or data.get("water_temp_c")
        or data.get("water_temperature")
        or data.get("wtemp")
    )

    # Hilfsfunktion: Wandelt den Wert sicher in eine Kommazahl um, oder gibt None zurück
    def _safe_float(x):
        try:
            return float(x) if x is not None else None
        except Exception:
            return None

    return _safe_float(temp), _safe_float(hum), _safe_float(wtemp)


def _normalize_reading(r: Reading) -> dict:
    """
    Formatiert ein einzelnes Messwert-Objekt (Reading) so, dass das Dashboard
    es direkt als JSON verarbeiten kann.
    """
    temp, hum, _ = _extract_values(r.data or {})
    return {
        "slug": r.sensor.slug,                  # Die eindeutige ID des Sensors
        "temperature": temp,
        "humidity": hum,
        "timestamp": _to_local_iso(r.timestamp), # Zeitstempel korrekt formatiert
    }


def _normalize_row(r: Reading) -> dict:
    """
    Bereitet eine Datenzeile speziell für die Historien-Tabelle auf.
    Hier brauche ich mehr Details als beim Dashboard (z.B. Ort und Typ).
    """
    temp, hum, wtemp = _extract_values(r.data or {})
    return {
        "timestamp": _to_local_iso(r.timestamp),
        "sensor": r.sensor.slug,
        "temperature": temp,
        "humidity": hum,
        "water_temperature": wtemp,
        "location": r.sensor.location or "",
        "type": r.sensor.sensor_type.name if r.sensor.sensor_type_id else "",
    }


def _get_query_slug(request: HttpRequest) -> Optional[str]:
    """
    Liest den Sensor-Namen aus der URL. Akzeptiert verschiedene Schreibweisen,
    falls ich mal 'id' statt 'slug' in der URL benutze.
    """
    return (
        request.GET.get("slug")
        or request.GET.get("sensor")
        or request.GET.get("sensor_slug")
        or request.GET.get("id")
    )


def _parse_iso_for_db(iso_str: str):
    """
    Das Gegenstück zu _to_local_iso: Wandelt einen String vom Frontend (z.B. vom Datums-Picker)
    in ein Datenbank-kompatibles Format um. Das ist knifflig, weil SQLite anders tickt als PostgreSQL.
    """
    if not iso_str:
        return None
    
    # Django versucht den String zu verstehen
    dt = parse_datetime(iso_str)
    if not dt:
        return None

    cur_tz = timezone.get_current_timezone()

    # Wenn Zeitzonen aktiv sind (USE_TZ=True)
    if settings.USE_TZ:
        if timezone.is_naive(dt):
            # Wenn keine Zone im String war, nehme ich an, es ist die aktuelle Serverzeit
            dt = timezone.make_aware(dt, cur_tz)
        # Ich rechne es in die Server-Zeitzone um
        return timezone.localtime(dt, cur_tz)

    # Wenn Zeitzonen deaktiviert sind (USE_TZ=False), speichert die DB "naive" Zeiten.
    if timezone.is_aware(dt):
        # Ich entferne die Zeitzonen-Info, rechne aber vorher noch korrekt um
        dt = dt.astimezone(cur_tz).replace(tzinfo=None)
    
    return dt


###############################################################################
# FRONTEND VIEWS
# Diese Views liefern keine JSON-Daten, sondern fertiges HTML an den Browser.
###############################################################################

@ensure_csrf_cookie
def frontend(request: HttpRequest) -> HttpResponse:
    """
    Zeigt das Haupt-Dashboard. 
    @ensure_csrf_cookie sorgt dafür, dass das Cookie für Sicherheits-Tokens gesetzt wird,
    damit JavaScript später API-Anfragen stellen darf.
    """
    return render(request, "telemetry/weboberflaeche.html")


@ensure_csrf_cookie
def historie(request: HttpRequest) -> HttpResponse:
    """
    Zeigt die Seite mit der Datentabelle und den Filtern.
    """
    return render(request, "telemetry/historie.html")


###############################################################################
# API: DATENAUFNAHME (INGEST)
# Hierhin senden die Sensoren ihre Daten (POST) oder das Dashboard fragt ab (GET).
###############################################################################

@csrf_exempt  # WICHTIG: Sensoren (ESP32 etc.) haben meist kein CSRF-Token, daher Ausnahme erlauben.
def ingest_view(request: HttpRequest) -> JsonResponse:
    """
    Die Haupt-Schnittstelle.
    POST: Speichert neue Daten.
    GET:  Liefert den allerletzten Messwert eines Sensors (für Live-Kacheln).
    """
    
    # --- POST: DATEN SPEICHERN ---
    if request.method == "POST":
        try:
            # Ich versuche, den Body als JSON zu lesen
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid json"}, status=400)

        # Daten auslesen (mit Fallbacks)
        slug = payload.get("slug") or payload.get("sensor") or payload.get("sensor_slug")
        sensor_name = payload.get("sensor_name") or slug
        st_name = payload.get("sensor_type") or "Generic"
        location = payload.get("location") or ""
        data = payload.get("data") or {}

        # Validierung: Ohne Slug geht nichts!
        if not slug:
            return JsonResponse({"error": "slug required"}, status=400)
        if not isinstance(data, dict):
            return JsonResponse({"error": "data must be object"}, status=400)

        try:
            # transaction.atomic() garantiert: Entweder alles wird gespeichert oder nichts.
            # Das verhindert halbe Datensätze bei Fehlern.
            with transaction.atomic():
                # 1. Sensor-Typ suchen oder erstellen
                stype, _ = SensorType.objects.get_or_create(name=st_name)
                
                # 2. Sensor suchen oder erstellen
                sensor, created = Sensor.objects.get_or_create(
                    slug=slug,
                    defaults={"name": sensor_name, "sensor_type": stype, "location": location},
                )

                # 3. Falls der Sensor schon existierte, prüfen wir, ob sich Metadaten geändert haben
                if not created:
                    changed = False
                    if sensor.sensor_type_id != stype.id:
                        sensor.sensor_type = stype
                        changed = True
                    if location and sensor.location != location:
                        sensor.location = location
                        changed = True
                    if sensor_name and sensor.name != sensor_name:
                        sensor.name = sensor_name
                        changed = True
                    
                    # Nur speichern, wenn sich wirklich etwas geändert hat (Performance)
                    if changed:
                        sensor.save(update_fields=["sensor_type", "location", "name"])

                # 4. Den eigentlichen Messwert speichern (Reading)
                dt = timezone.now() # Ich nutze die aktuelle Serverzeit als Zeitstempel
                reading = Reading.objects.create(sensor=sensor, data=data, timestamp=dt)

        except Exception as e:
            # Bei Fehlern (z.B. Datenbank weg) sauber antworten
            return JsonResponse({"error": "ingest failed", "detail": str(e)}, status=500)

        # Erfolgsmeldung zurücksenden
        return JsonResponse({"status": "ok", "id": reading.id, "timestamp": _to_local_iso(reading.timestamp)})

    # --- GET: LETZTEN WERT LADEN ---
    if request.method == "GET":
        slug = _get_query_slug(request)
        if not slug:
            return JsonResponse({"error": "slug required"}, status=400)

        try:
            sensor = Sensor.objects.get(slug=slug)
        except Sensor.DoesNotExist:
            return JsonResponse({"error": "sensor not found"}, status=404)

        # Ich hole nur den neuesten Eintrag (.first() nach order_by desc)
        # .only() und .select_related() optimieren die Datenbankabfrage
        latest = sensor.readings.order_by("-timestamp").only("id", "timestamp", "data", "sensor__slug").select_related("sensor").first()
        
        if not latest:
            return JsonResponse({"error": "no data"}, status=404)

        return JsonResponse(_normalize_reading(latest))

    # Wenn weder GET noch POST
    return JsonResponse({"error": "method not allowed"}, status=405)


def water_latest(request: HttpRequest) -> JsonResponse:
    """
    Spezial-View für das Wasser-Widget. Funktioniert fast wie ingest(GET),
    gibt aber ein vereinfachtes JSON zurück.
    """
    slug = _get_query_slug(request) or "wasser"
    try:
        sensor = Sensor.objects.get(slug=slug)
    except Sensor.DoesNotExist:
        return JsonResponse({"error": "sensor not found"}, status=404)

    latest = sensor.readings.order_by("-timestamp").only("id", "timestamp", "data", "sensor__slug").select_related("sensor").first()
    if not latest:
        return JsonResponse({"error": "no data"}, status=404)

    payload = _normalize_reading(latest)
    # Ich baue eine Antwort, die nur das enthält, was das Wasser-Widget braucht
    return JsonResponse({
        "slug": payload["slug"],
        "temperature": payload["temperature"],
        "timestamp": payload["timestamp"],
    })


###############################################################################
# API: HISTORIE & LISTEN
# Diese Views versorgen die Historien-Tabelle mit Daten.
###############################################################################

def sensors_list(request: HttpRequest) -> JsonResponse:
    """
    Liefert eine Liste aller bekannten Sensoren.
    Wird z.B. genutzt, um das Dropdown-Menü im Filter zu füllen.
    """
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    # Datenbankabfrage optimieren
    qs = (
        Sensor.objects.select_related("sensor_type")
        .only("id", "name", "slug", "sensor_type__name", "location")
        .order_by("slug")
    )

    # Liste zusammenbauen
    items = [{
        "id": s.id,
        "name": s.name,
        "slug": s.slug,
        "type": s.sensor_type.name if s.sensor_type_id else "",
        "location": s.location or "",
        "is_active": True,
    } for s in qs]

    return JsonResponse(items, safe=False)


def readings_view(request: HttpRequest) -> JsonResponse:
    """
    Die mächtige Abfrage für die Tabelle. Unterstützt:
    - Filter nach Sensor
    - Suche (Text)
    - Zeitraum (von/bis)
    - Paginierung (Seite X von Y)
    """
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    # Parameter aus der URL lesen
    sensor_slug = (request.GET.get("sensor") or request.GET.get("slug") or "").strip()
    qtext = (request.GET.get("q") or "").strip() # Suchtext

    # Zeitfilter parsen (mit meiner Helper-Funktion von oben)
    from_raw = request.GET.get("from") or ""
    to_raw   = request.GET.get("to") or ""
    dt_from = _parse_iso_for_db(from_raw)
    dt_to   = _parse_iso_for_db(to_raw)

    # Paginierung berechnen (Default: Seite 1, 100 Einträge)
    try:
        page = max(1, int(request.GET.get("page", "1")))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get("page_size", "100"))
        page_size = min(max(page_size, 1), 1000) # Sicherheit: Max 1000 Zeilen pro Abruf
    except ValueError:
        page_size = 100

    # --- START DER DATENBANK-ABFRAGE ---
    qs = (
        Reading.objects.select_related("sensor", "sensor__sensor_type")
        .only("timestamp", "data", "sensor__slug", "sensor__location", "sensor__sensor_type__name")
    )

    # Filter anwenden (nur wenn Parameter gesetzt sind)
    if sensor_slug:
        qs = qs.filter(sensor__slug=sensor_slug)
    if dt_from:
        qs = qs.filter(timestamp__gte=dt_from) # gte = Greater Than or Equal (>=)
    if dt_to:
        qs = qs.filter(timestamp__lte=dt_to)   # lte = Less Than or Equal (<=)
    
    # Textsuche über mehrere Felder (ODER-Verknüpfung mit Q-Objekten)
    if qtext:
        qs = qs.filter(
            Q(sensor__slug__icontains=qtext) |
            Q(sensor__name__icontains=qtext) |
            Q(sensor__location__icontains=qtext) |
            Q(sensor__sensor_type__name__icontains=qtext)
        )

    # Neueste zuerst
    qs = qs.order_by("-timestamp")

    # --- PAGINIERUNG & SLICING ---
    total = qs.count()                  # Gesamtanzahl der Treffer zählen
    start = (page - 1) * page_size      # Start-Index berechnen
    end = start + page_size             # End-Index berechnen
    
    # Hier passiert der eigentliche Datenbank-Zugriff für die Datensätze (limitiert durch Slice)
    page_qs = list(qs[start:end])

    # Daten für die Ausgabe normalisieren
    results = [_normalize_row(r) for r in page_qs]

    # JSON-Antwort bauen
    return JsonResponse({
        "results": results,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": end < total,    # Gibt es noch eine weitere Seite?
        "has_prev": start > 0,      # Gibt es eine vorherige Seite?
    })