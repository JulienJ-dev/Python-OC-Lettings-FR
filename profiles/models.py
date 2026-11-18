"""Define the additional information attached to a Django user."""

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Associate one user with an optional favorite city."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_city = models.CharField(max_length=64, blank=True)

    def __str__(self):
        """Return the associated username as the profile's readable string."""
        return self.user.username
