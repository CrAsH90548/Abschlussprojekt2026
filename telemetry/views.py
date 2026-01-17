from __future__ import annotations

import json
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from .models import SensorType, Sensor, Reading


# ---------- Helpers ----------

def _to_local_iso(ts) -> str:
    """
    Gibt den Timestamp als lokale ISO-Zeit (Europe/Berlin) zurück – robust für USE_TZ True/False.
    """
    # Wenn USE_TZ=True: mit TZ arbeiten und in aktuelle TZ (Europe/Berlin) konvertieren
    if settings.USE_TZ:
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, timezone.get_current_timezone())
        return timezone.localtime(ts, timezone.get_current_timezone()).isoformat()
    # Wenn USE_TZ=False: ts ist naiv (lokale Zeit); einfach isoformat()
    return ts.isoformat()


def _extract_values(data: dict):
    """
    Liest Temperatur/Luftfeuchte/Wassertemperatur aus Reading.data (robust gegen verschiedene Keys).
    """
    if not isinstance(data, dict):
        return None, None, None

    temp = (
        data.get("temperature_c")
        or data.get("temp_c")
        or data.get("temperature")
        or data.get("temp")
    )
    hum = (
        data.get("humidity_percent")
        or data.get("humidity")
        or data.get("hum")
    )
    wtemp = (
        data.get("water_temperature_c")
        or data.get("water_temp_c")
        or data.get("water_temperature")
        or data.get("wtemp")
    )

    def _safe_float(x):
        try:
            return float(x) if x is not None else None
        except Exception:
            return None

    return _safe_float(temp), _safe_float(hum), _safe_float(wtemp)


def _normalize_reading(r: Reading) -> dict:
    """
    Normalisierung für Live-Kacheln im Dashboard.
    """
    temp, hum, _ = _extract_values(r.data or {})
    return {
        "slug": r.sensor.slug,
        "temperature": temp,
        "humidity": hum,
        "timestamp": _to_local_iso(r.timestamp),
    }


def _normalize_row(r: Reading) -> dict:
    """
    Normalisierung für die Historien-Tabelle (historie.html).
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
    """Akzeptiere mehrere Query-Namen, falls Client/Raspi abweichen."""
    return (
        request.GET.get("slug")
        or request.GET.get("sensor")
        or request.GET.get("sensor_slug")
        or request.GET.get("id")
    )


def _parse_iso_for_db(iso_str: str):
    """
    Parsed ISO-String robust für USE_TZ True/False.

    - Wenn USE_TZ=True:
        * Falls Eingabe naive ist → als aktuelle TZ interpretieren (Europe/Berlin)
        * Falls tz-aware → in aktuelle TZ konvertieren
    - Wenn USE_TZ=False:
        * tz-aware Eingaben werden in aktuelle TZ konvertiert und dann tzinfo entfernt
        * naive Eingaben unverändert (naive lokale Zeit)
    """
    if not iso_str:
        return None
    dt = parse_datetime(iso_str)
    if not dt:
        return None

    cur_tz = timezone.get_current_timezone()

    if settings.USE_TZ:
        if timezone.is_naive(dt):
            # naive → current timezone anheften
            dt = timezone.make_aware(dt, cur_tz)
        # in aktuelle TZ normalisieren
        return timezone.localtime(dt, cur_tz)

    # USE_TZ == False → DB arbeitet mit naiver lokaler Zeit
    if timezone.is_aware(dt):
        # in lokale TZ und tzinfo entfernen
        dt = dt.astimezone(cur_tz).replace(tzinfo=None)
    else:
        # bereits naive → so lassen
        pass
    return dt


# ---------- Frontend ----------

@ensure_csrf_cookie
def frontend(request: HttpRequest) -> HttpResponse:
    """
    Liefert die Weboberfläche (Dashboard).
    Template: telemetry/templates/telemetry/weboberflaeche.html
    """
    return render(request, "telemetry/weboberflaeche.html")


@ensure_csrf_cookie
def historie(request: HttpRequest) -> HttpResponse:
    """
    Liefert die Historien-Ansicht.
    Template: telemetry/templates/telemetry/historie.html
    """
    return render(request, "telemetry/historie.html")


# ---------- API: Live (bestehend) ----------

@csrf_exempt
def ingest_view(request: HttpRequest) -> JsonResponse:
    """
    POST /api/ingest
      JSON:
        {
          "slug": "raum",
          "sensor_type": "DHT22",        # optional
          "sensor_name": "Lab-DHT22-1",  # optional
          "location": "Labor",           # optional
          "data": {"temperature_c": 22.3, "humidity_percent": 58.1}
        }

    GET /api/ingest?slug=raum  → letztes Reading fürs Dashboard
    """
    if request.method == "POST":
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid json"}, status=400)

        slug = payload.get("slug") or payload.get("sensor") or payload.get("sensor_slug")
        sensor_name = payload.get("sensor_name") or slug
        st_name = payload.get("sensor_type") or "Generic"
        location = payload.get("location") or ""
        data = payload.get("data") or {}

        if not slug:
            return JsonResponse({"error": "slug required"}, status=400)
        if not isinstance(data, dict):
            return JsonResponse({"error": "data must be object"}, status=400)

        try:
            with transaction.atomic():
                stype, _ = SensorType.objects.get_or_create(name=st_name)
                sensor, created = Sensor.objects.get_or_create(
                    slug=slug,
                    defaults={"name": sensor_name, "sensor_type": stype, "location": location},
                )

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
                    if changed:
                        sensor.save(update_fields=["sensor_type", "location", "name"])

                # SERVERZEIT (naiv bei USE_TZ=False, aware bei USE_TZ=True)
                dt = timezone.now()
                reading = Reading.objects.create(sensor=sensor, data=data, timestamp=dt)

        except Exception as e:
            return JsonResponse({"error": "ingest failed", "detail": str(e)}, status=500)

        return JsonResponse({"status": "ok", "id": reading.id, "timestamp": _to_local_iso(reading.timestamp)})

    if request.method == "GET":
        slug = _get_query_slug(request)
        if not slug:
            return JsonResponse({"error": "slug required"}, status=400)

        try:
            sensor = Sensor.objects.get(slug=slug)
        except Sensor.DoesNotExist:
            return JsonResponse({"error": "sensor not found"}, status=404)

        latest = sensor.readings.order_by("-timestamp").only("id", "timestamp", "data", "sensor__slug").select_related("sensor").first()
        if not latest:
            return JsonResponse({"error": "no data"}, status=404)

        return JsonResponse(_normalize_reading(latest))

    return JsonResponse({"error": "method not allowed"}, status=405)


def water_latest(request: HttpRequest) -> JsonResponse:
    """
    GET /api/water/latest?slug=wasser
    Liefert letztes Reading (typisch nur Temperatur) fürs Wasser.
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
    return JsonResponse({
        "slug": payload["slug"],
        "temperature": payload["temperature"],
        "timestamp": payload["timestamp"],
    })


# ---------- API: Historie (NEU) ----------

def sensors_list(request: HttpRequest) -> JsonResponse:
    """
    GET /api/sensors
    Antwort: [{id, name, slug, type, location, is_active}]
    """
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    qs = (
        Sensor.objects.select_related("sensor_type")
        .only("id", "name", "slug", "sensor_type__name", "location")
        .order_by("slug")
    )

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
    GET /api/readings?sensor=<slug>&from=<iso>&to=<iso>&q=<text>&page=<n>&page_size=<n>
    Antwort:
      {
        "results": [...],
        "page": 1,
        "page_size": 100,
        "total": 1234,
        "has_next": true/false,
        "has_prev": true/false
      }
    """
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    sensor_slug = (request.GET.get("sensor") or request.GET.get("slug") or "").strip()
    qtext = (request.GET.get("q") or "").strip()

    # Zeitraum parsen (robust für USE_TZ True/False)
    from_raw = request.GET.get("from") or ""
    to_raw   = request.GET.get("to") or ""
    dt_from = _parse_iso_for_db(from_raw)
    dt_to   = _parse_iso_for_db(to_raw)

    # Paging
    try:
        page = max(1, int(request.GET.get("page", "1")))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get("page_size", "100"))
        page_size = min(max(page_size, 1), 1000)
    except ValueError:
        page_size = 100

    # Basis-Query (schlank)
    qs = (
        Reading.objects.select_related("sensor", "sensor__sensor_type")
        .only("timestamp", "data", "sensor__slug", "sensor__location", "sensor__sensor_type__name")
    )

    if sensor_slug:
        qs = qs.filter(sensor__slug=sensor_slug)
    if dt_from:
        qs = qs.filter(timestamp__gte=dt_from)
    if dt_to:
        qs = qs.filter(timestamp__lte=dt_to)
    if qtext:
        qs = qs.filter(
            Q(sensor__slug__icontains=qtext) |
            Q(sensor__name__icontains=qtext) |
            Q(sensor__location__icontains=qtext) |
            Q(sensor__sensor_type__name__icontains=qtext)
        )

    qs = qs.order_by("-timestamp")

    # Count + Slice
    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    page_qs = list(qs[start:end])

    results = [_normalize_row(r) for r in page_qs]

    return JsonResponse({
        "results": results,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": end < total,
        "has_prev": start > 0,
    })
