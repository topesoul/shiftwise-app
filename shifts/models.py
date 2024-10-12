# shifts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Agency(models.Model):
    """
    Represents an agency managing multiple shifts.
    """
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    agency_code = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Agencies"

    def __str__(self):
        return f"{self.agency_code} - {self.name}"

    def save(self, *args, **kwargs):
        """
        Generates a unique agency code if not provided.
        """
        if not self.agency_code:
            base_code = slugify(self.name)[:10]
            unique_code = base_code
            num = 1
            while Agency.objects.filter(agency_code=unique_code).exists():
                unique_code = f"{base_code}{num}"
                num += 1
                if len(unique_code) > 20:
                    unique_code = unique_code[:20]
            self.agency_code = unique_code
        super().save(*args, **kwargs)


class Shift(models.Model):
    """
    Represents a work shift managed by an agency.
    """
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_date = models.DateField()
    capacity = models.PositiveIntegerField(default=1)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    postcode = models.CharField(max_length=10)
    address_line1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['shift_date', 'start_time']

    def __str__(self):
        return f"{self.name} on {self.shift_date} for {self.agency.name}"

    def clean(self):
        """
        Validates the Shift instance before saving.
        """
        super().clean()
        if self.shift_date and self.shift_date < timezone.now().date():
            raise ValidationError('Shift date cannot be in the past.')
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after the start time.')
        start_dt = timezone.datetime.combine(self.shift_date, self.start_time)
        end_dt = timezone.datetime.combine(self.shift_date, self.end_time)
        duration = (end_dt - start_dt).total_seconds() / 3600
        if duration <= 0:
            duration += 24  # Adjust for overnight shifts
        if duration > 24:
            raise ValidationError('Shift duration cannot exceed 24 hours.')

    @property
    def available_slots(self):
        """
        Returns the number of available slots for the shift.
        """
        assigned_count = self.shiftassignment_set.count()
        return self.capacity - assigned_count

    @property
    def is_full(self):
        """
        Returns True if the shift is fully booked.
        """
        return self.available_slots <= 0


class ShiftAssignment(models.Model):
    """
    Associates a worker with a specific shift.
    """
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('worker', 'shift')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.worker.username} assigned to {self.shift.name} on {self.shift.shift_date}"

    def clean(self):
        """
        Validates the ShiftAssignment instance before saving.
        """
        super().clean()
        if not hasattr(self.worker, 'profile'):
            raise ValidationError("Worker does not have an associated profile.")
        if self.worker.profile.agency != self.shift.agency:
            raise ValidationError("Workers can only be assigned to shifts within their agency.")
        if self.shift.is_full:
            raise ValidationError("This shift is already fully booked.")
