# notifications/models.py

from django.db import models
from django.conf import settings

class Notification(models.Model):
    """
    Represents a notification for a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.CharField(max_length=255)
    icon = models.CharField(max_length=50, default="fas fa-info-circle")
    url = models.URLField(blank=True, null=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
