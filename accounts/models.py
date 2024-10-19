from django.db import models
from django.contrib.auth.models import User
from shifts.models import Agency

class Profile(models.Model):
    """
    Extends the User model with additional information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def __str__(self):
        return f"{self.user.username}'s Profile"
