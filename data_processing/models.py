from django.db import models
import time

class DeviceManager(models.Model):
    # id will be automatically created by django
    latitude = models.FloatField()
    longitude = models.FloatField()
    doi = models.DateField() # date of installation
    status = models.BooleanField(default=True)

class ForecastModel(models.Model):
    CHOICE = (
        (0, "heavy"),
        (1, "idle"),
        (2, "light"),
        (3, "medium"),
    )
    timestamp = models.BigIntegerField()
    forecast = models.IntegerField(choices=CHOICE)
    noise_level = models.IntegerField()
    device = models.ForeignKey(DeviceManager, on_delete=models.CASCADE)

class EmergencyData(models.Model):
    device_id = models.IntegerField()
    timestamp = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            self.timestamp = int(time.time() * 1000)
        super().save(*args, **kwargs)

    def _str_(self):
        return f"Emergency Request from {self.device_id} at {self.timestamp}"