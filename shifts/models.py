# /workspace/shiftwise/shifts/models.py

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from .validators import validate_image

User = settings.AUTH_USER_MODEL


class TimestampedModel(models.Model):
    """
    Abstract model to track when records are created and last updated.
    Inherited by other models.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Shift(TimestampedModel):
    """
    Represents a work shift managed by an agency.
    """

    # Shift Type Choices
    REGULAR = "regular"
    MORNING_SHIFT = "morning_shift"
    DAY_SHIFT = "day_shift"
    NIGHT_SHIFT = "night_shift"
    BANK_HOLIDAY = "bank_holiday"
    EMERGENCY_SHIFT = "emergency_shift"
    OVERTIME = "overtime"

    SHIFT_TYPE_CHOICES = [
        (REGULAR, "Regular"),
        (MORNING_SHIFT, "Morning Shift"),
        (DAY_SHIFT, "Day Shift"),
        (NIGHT_SHIFT, "Night Shift"),
        (BANK_HOLIDAY, "Bank Holiday"),
        (EMERGENCY_SHIFT, "Emergency Shift"),
        (OVERTIME, "Overtime"),
    ]

    # Shift Status Choices
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELED = "canceled"
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELED, "Canceled"),
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=255)
    shift_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    end_date = models.DateField(
        help_text="Specify the date when the shift ends.", null=True, blank=True
    )
    is_overnight = models.BooleanField(
        default=False, help_text="Check this box if the shift spans into the next day."
    )
    capacity = models.PositiveIntegerField(default=1)
    agency = models.ForeignKey(
        "accounts.Agency", on_delete=models.CASCADE, related_name="shifts"
    )
    postcode = models.CharField(max_length=20, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="UK")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    shift_type = models.CharField(
        max_length=50, choices=SHIFT_TYPE_CHOICES, default=REGULAR
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    is_completed = models.BooleanField(default=False)
    completion_time = models.DateTimeField(null=True, blank=True)
    signature = models.ImageField(
        upload_to="signatures/", null=True, blank=True, validators=[validate_image]
    )
    duration = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["shift_date", "start_time"]
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"

    def __str__(self):
        return f"{self.name} on {self.shift_date}"

    def clean(self, skip_date_validation=False):
        """
        Validates the Shift instance before saving.
        Allows shifts to span into the next day within a 24-hour period.
        The 'skip_date_validation' flag allows bypassing date checks when completing a shift.
        """
        super().clean()

        # Ensure shift date is not in the past unless skipping validation
        if not skip_date_validation:
            if self.shift_date and self.shift_date < timezone.now().date():
                raise ValidationError("Shift date cannot be in the past.")

        # Ensure end date is provided
        if not self.end_date:
            raise ValidationError("End date must be provided.")

        # Ensure end date is not before shift date
        if self.end_date < self.shift_date:
            raise ValidationError("End date cannot be before shift date.")

        # Ensure all date and time fields are provided
        if (
            not self.shift_date
            or not self.end_date
            or not self.start_time
            or not self.end_time
        ):
            raise ValidationError("All date and time fields must be provided.")

        # Combine start and end datetime objects
        start_dt = timezone.make_aware(
            timezone.datetime.combine(self.shift_date, self.start_time),
            timezone.get_current_timezone(),
        )
        end_dt = timezone.make_aware(
            timezone.datetime.combine(self.end_date, self.end_time),
            timezone.get_current_timezone(),
        )

        # Handle overnight shifts
        if self.is_overnight:
            if end_dt <= start_dt:
                end_dt += timezone.timedelta(days=1)
        else:
            # Non-overnight shifts: end_dt should be after start_dt
            if end_dt <= start_dt:
                raise ValidationError("End time must be after start time for non-overnight shifts.")

        # Calculate duration in hours
        duration = (end_dt - start_dt).total_seconds() / 3600

        # Validate duration does not exceed 24 hours
        if duration > 24:
            raise ValidationError("Shift duration cannot exceed 24 hours.")

        self.duration = duration

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure clean is called.
        Allows passing 'skip_date_validation' through kwargs.
        """
        skip_date_validation = kwargs.pop("skip_date_validation", False)
        self.clean(skip_date_validation=skip_date_validation)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns the URL to access a particular shift instance.
        """
        return reverse("shifts:shift_detail", kwargs={"pk": self.pk})

    @property
    def available_slots(self):
        """
        Returns the number of available slots for the shift.
        """
        assigned_count = self.assignments.filter(
            status=ShiftAssignment.CONFIRMED
        ).count()
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
    """

    # Assignment Status Choices
    CONFIRMED = "confirmed"
    CANCELED = "canceled"

    STATUS_CHOICES = [
        (CONFIRMED, "Confirmed"),
        (CANCELED, "Canceled"),
    ]

    # Role Choices
    ROLE_CHOICES = (
        ("Staff", "Staff"),
        ("Manager", "Manager"),
        ("Admin", "Admin"),
        ("Care Worker", "Healthcare Worker"),
        ("Kitchen Staff", "Kitchen"),
        ("Front Office Staff", "Front Office"),
        ("Receptionist", "Receptionist"),
        ("Chef", "Chef"),
        ("Waiter", "Waiter"),
        ("Dishwasher", "Dishwasher"),
        ("Laundry Staff", "Laundry"),
        ("Housekeeping Staff", "Housekeeping"),
        ("Other", "Other"),
    )

    # Attendance Status Choices
    ATTENDANCE_STATUS_CHOICES = (
        ("attended", "Attended"),
        ("late", "Late"),
        ("no_show", "No Show"),
    )

    worker = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shift_assignments"
    )
    shift = models.ForeignKey(
        "Shift", on_delete=models.CASCADE, related_name="assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=100, default="Staff", choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CONFIRMED)
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="Select attendance status after the shift.",
    )
    completion_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    completion_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    completion_time = models.DateTimeField(null=True, blank=True)
    signature = models.ImageField(
        upload_to="shift_signatures/",
        null=True,
        blank=True,
        validators=[validate_image],
    )

    class Meta:
        unique_together = ("worker", "shift")
        ordering = ["-assigned_at"]
        verbose_name = "Shift Assignment"
        verbose_name_plural = "Shift Assignments"

    def __str__(self):
        return f"{self.worker} assigned to {self.shift.name} on {self.shift.shift_date}"

    def clean(self):
        """
        Validates the ShiftAssignment instance before saving.
        """
        super().clean()

        # Ensure worker has an associated profile
        if not hasattr(self.worker, "profile"):
            raise ValidationError("Worker does not have an associated profile.")

        # Ensure worker's agency matches the shift's agency
        if self.worker.profile.agency != self.shift.agency:
            raise ValidationError(
                "Workers can only be assigned to shifts within their agency."
            )

        # Prevent assignment if shift is full and status is CONFIRMED
        if self.shift.is_full and self.status == self.CONFIRMED:
            raise ValidationError("This shift is already fully booked.")

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure clean is called.
        """
        self.clean()
        super().save(*args, **kwargs)


class StaffPerformance(models.Model):
    """
    Represents the performance metrics of a staff member.
    """

    STATUS_CHOICES = [
        ("Excellent", "Excellent"),
        ("Good", "Good"),
        ("Average", "Average"),
        ("Poor", "Poor"),
    ]

    worker = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="performances"
    )
    shift = models.ForeignKey(
        "Shift", on_delete=models.CASCADE, related_name="performances"
    )
    wellness_score = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Score between 0 and 100"
    )
    performance_rating = models.DecimalField(
        max_digits=3, decimal_places=1, help_text="Rating out of 5"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Average")
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("worker", "shift")
        verbose_name = "Staff Performance"
        verbose_name_plural = "Staff Performances"

    def __str__(self):
        return f"Performance of {self.worker.username} for Shift {self.shift.id}"
