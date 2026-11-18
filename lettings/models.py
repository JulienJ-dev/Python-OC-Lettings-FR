"""Define property addresses and the lettings associated with them."""

from django.db import models
from django.core.validators import MaxValueValidator, MinLengthValidator


class Address(models.Model):
    """Store a postal address, including its state and ISO country code."""

    number = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    street = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    state = models.CharField(max_length=2, validators=[MinLengthValidator(2)])
    zip_code = models.PositiveIntegerField(validators=[MaxValueValidator(99999)])
    country_iso_code = models.CharField(max_length=3, validators=[MinLengthValidator(3)])

    class Meta:
        """Use the correct English plural in the administration site."""

        verbose_name_plural = 'Addresses'

    def __str__(self):
        """Return the street number and street name as a readable string."""
        return f'{self.number} {self.street}'


class Letting(models.Model):
    """Store a rental title linked to a unique postal address."""

    title = models.CharField(max_length=256)
    address = models.OneToOneField(Address, on_delete=models.CASCADE)

    def __str__(self):
        """Return the letting title as its readable string representation."""
        return self.title
