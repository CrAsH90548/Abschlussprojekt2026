from django.db import models
from django.utils import timezone

class SensorType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Sensor(models.Model):
    name = models.CharField(max_length=100)     # unique=True entfernt
    slug = models.SlugField(max_length=120, unique=True)
    sensor_type = models.ForeignKey(SensorType, on_delete=models.PROTECT)
    location = models.CharField(max_length=200, blank=True)
 
    def __str__(self):
        return self.name

class Reading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="readings")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    data = models.JSONField()  # z.B. {"temperature_c": 22.3, "humidity_percent": 40.5}

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.sensor.name} @ {self.timestamp.isoformat()}"
