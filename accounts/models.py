# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('agency_manager', 'Agency Manager'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='profile')
    agency = models.ForeignKey('shifts.Agency', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='UK')
    postcode = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    travel_radius = models.IntegerField(default=10, help_text="Travel radius in kilometers")
    location = gis_models.PointField(geography=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
