from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from geopy.distance import geodesic

# Create your models here.
class Shift(models.Model):
    # Shift Name
    name = models.CharField(max_length=100)

    # Mandatory fields for managing shift times
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_date = models.DateField()

    # Address fields for shift location
    postcode = models.CharField(max_length=10)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='UK')

    # Location fields for proximity calculation
    latitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    longitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])

    # If a shift requires specific skills or qualifications
    required_skills = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} on {self.shift_date}"

    # Function to calculate the distance from staff to the shift location
    def calculate_distance(self, worker_latitude, worker_longitude):
        if self.latitude and self.longitude and worker_latitude and worker_longitude:
            shift_location = (self.latitude, self.longitude)
            worker_location = (worker_latitude, worker_longitude)
            return geodesic(shift_location, worker_location).miles  # Returns the distance in miles
        return None

    # Ensure the shift time is valid
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after the start time.')