from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid


class TimestampedModel(models.Model):
    """
    Abstract model to track when records are created and last updated.
    This is inherited by other models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Agency(TimestampedModel):
    """
    Represents an agency managing multiple shifts.
    Inherits from TimestampedModel to track creation and update times.
    """
    name = models.CharField(max_length=100)
    address_line1 = models.CharField(max_length=255, default="Unknown Address")
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, default="Unknown City")
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    agency_code = models.CharField(max_length=20, unique=True, blank=True)
    agency_type = models.CharField(
        max_length=50,
        choices=[('staffing', 'Staffing'), ('healthcare', 'Healthcare')],
        default='staffing'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Agencies"

    def __str__(self):
        return f"{self.agency_code} - {self.name}"

    def save(self, *args, **kwargs):
        """
        Generates a unique agency code using UUID if not provided.
        """
        if not self.agency_code:
            self.agency_code = f"AG-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class Shift(TimestampedModel):
    """
    Represents a work shift managed by an agency.
    Inherits from TimestampedModel to track creation and update times.
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
    shift_type = models.CharField(
        max_length=50,
        choices=[('regular', 'Regular'), ('overtime', 'Overtime'), ('holiday', 'Holiday')],
        default='regular'
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('canceled', 'Canceled')],
        default='pending'
    )
    duration = models.FloatField(null=True, blank=True)

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

        # Calculate duration of the shift
        start_dt = timezone.datetime.combine(self.shift_date, self.start_time)
        end_dt = timezone.datetime.combine(self.shift_date, self.end_time)
        duration = (end_dt - start_dt).total_seconds() / 3600
        if duration <= 0:
            duration += 24
        if duration > 24:
            raise ValidationError('Shift duration cannot exceed 24 hours.')
        self.duration = duration

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


class ShiftAssignment(TimestampedModel):
    """
    Associates a worker with a specific shift.
    Inherits from TimestampedModel to track creation and update times.
    """
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=100, default='Staff')
    status = models.CharField(
        max_length=20,
        choices=[('confirmed', 'Confirmed'), ('canceled', 'Canceled')],
        default='confirmed'
    )

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