from django.db import models

class DeviceManager(models.Model):
    # id will be automatically created by django
    latitude = models.FloatField()
    longitude = models.FloatField()
    doi = models.DateField() # date of installation
    status = models.BooleanField(default=True)

# class AudioData(models.Model):
#     CHOICE = (
#         (0, 'Idle'),
#         (1, 'light'),
#         (2, 'medium'),
#         (3, 'heavy'),
#     )
#     date_time = models.DateTimeField()
#     audio = models.CharField(max_length=100)
#     # audio = models.FileField(upload_to='audio/')
#     mfcc = models.CharField(max_length=100)
#     # mfcc = models.FileField(upload_to="mfcc/")
#     density = models.IntegerField(choices=CHOICE)
#     device = models.ForeignKey(DeviceManager, on_delete=models.CASCADE)
