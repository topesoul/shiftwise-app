from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from geopy.distance import geodesic
from django.core.exceptions import ValidationError

# Create your models here.

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_date = models.DateField()

    # Capacity (how many workers are needed)
    capacity = models.PositiveIntegerField(default=1)

    # Address and location details
    postcode = models.CharField(max_length=10)
    address_line1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

    # Coordinates for geolocation purposes
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} on {self.shift_date}"

    # Validation to ensure start time is before end time and handle shifts crossing midnight
    def clean(self):
        super().clean()
        
        if self.shift_date:
            if self.shift_date < timezone.now().date():
                raise ValidationError('Shift date cannot be in the past.')
        
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after the start time.')

        start_dt = timezone.datetime.combine(self.shift_date, self.start_time)
        end_dt = timezone.datetime.combine(self.shift_date, self.end_time)

        duration = (end_dt - start_dt).total_seconds() / 3600  # Duration in hours
        if duration <= 0:
            duration += 24  # Adjust for overnight shifts

        if duration > 24:
            raise ValidationError('Shift duration cannot exceed 24 hours.')

    @property
    def available_slots(self):
        """Returns the number of available slots for the shift."""
        assigned_count = self.shiftassignment_set.count()  # Count workers assigned
        return self.capacity - assigned_count

    @property
    def is_full(self):
        """Returns True if the shift is fully booked."""
        return self.available_slots <= 0

# ShiftAssignment model (for linking shifts to staff)
class ShiftAssignment(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.worker.username} assigned to {self.shift.name} on {self.shift.shift_date}"

    class Meta:
        unique_together = ('worker', 'shift')  # Ensure a worker can't be assigned to the same shift twice