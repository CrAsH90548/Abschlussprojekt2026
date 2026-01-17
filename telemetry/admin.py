from django.contrib import admin
from .models import SensorType, Sensor, Reading

@admin.register(SensorType)
class SensorTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "location")
    list_display = ("name", "sensor_type", "location")

@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("sensor", "timestamp")
    list_filter = ("sensor",)
