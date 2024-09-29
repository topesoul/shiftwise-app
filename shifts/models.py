from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from geopy.distance import geodesic
from django.core.exceptions import ValidationError

# Create your models here.
class Shift(models.Model):
    # Name of the shift
    name = models.CharField(max_length=100)

    # Date and time fields (required)
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_date = models.DateField()

    # Address fields
    postcode = models.CharField(max_length=10)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='UK')

    # Location fields for proximity checks
    latitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )

    def __str__(self):
        return f"{self.name} on {self.shift_date}"

    def calculate_distance(self, worker_latitude, worker_longitude):
        if self.latitude and self.longitude and worker_latitude and worker_longitude:
            shift_location = (self.latitude, self.longitude)
            worker_location = (worker_latitude, worker_longitude)
            return geodesic(shift_location, worker_location).miles
        return None

    def clean(self):
        super().clean()
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after the start time.')

        # Calculate duration
        start_dt = timezone.datetime.combine(self.shift_date, self.start_time)
        end_dt = timezone.datetime.combine(self.shift_date, self.end_time)

        duration = (end_dt - start_dt).total_seconds() / 3600  # Duration in hours

        if duration <= 0:
            duration += 24  # Adjust for shifts that end the next day

        if duration > 24:
            raise ValidationError('Shift duration cannot exceed 24 hours.')
