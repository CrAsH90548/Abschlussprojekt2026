from django.urls import path
from .views import (
    frontend, historie,
    ingest_view, water_latest,
    sensors_list, readings_view,
)

urlpatterns = [
    path("", frontend, name="frontend"),                        # Dashboard
    path("historie/", historie, name="historie"),               # Historie-UI

    # API
    path("api/ingest/", ingest_view, name="ingest_with_slash"),
    path("api/water/latest", water_latest, name="water_latest"),
    path("api/sensors", sensors_list, name="sensors_list"),
    path("api/readings", readings_view, name="readings_view"),
]
