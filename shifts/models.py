from django.db import models

# Create your models here.
from django.db import models

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_date = models.DateField()
    postcode = models.CharField(max_length=10, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} on {self.shift_date}"
