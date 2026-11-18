"""Regression checks for letting pages, routes and administration."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import resolve, reverse

from . import views
from .models import Address, Letting


class LettingsTests(TestCase):
    """Keep the existing letting features available after the move."""

    @classmethod
    def setUpTestData(cls):
        """Create a letting and its address in the new application."""
        cls.address = Address.objects.create(
            number=10, street='Main Street', city='Irvine', state='CA',
            zip_code=92618, country_iso_code='USA',
        )
        cls.letting = Letting.objects.create(title='Holiday home', address=cls.address)

    def test_namespaced_routes(self):
        """Preserve public paths and route them to the new views."""
        self.assertEqual(reverse('lettings:index'), '/lettings/')
        detail = reverse('lettings:letting', kwargs={'letting_id': self.letting.pk})
        self.assertEqual(detail, '/lettings/{}/'.format(self.letting.pk))
        self.assertEqual(resolve('/lettings/').func, views.index)
        self.assertEqual(resolve(detail).func, views.letting)

    def test_index(self):
        """Display the existing list using the application template."""
        response = self.client.get(reverse('lettings:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lettings/index.html')
        self.assertContains(response, self.letting.title)
        self.assertContains(response, reverse(
            'lettings:letting', kwargs={'letting_id': self.letting.pk},
        ))

    def test_detail(self):
        """Display the letting and its related address."""
        response = self.client.get(reverse(
            'lettings:letting', kwargs={'letting_id': self.letting.pk},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lettings/letting.html')
        self.assertContains(response, self.letting.title)
        self.assertContains(response, str(self.address))

    def test_empty_index(self):
        """Explain that no lettings are available when the list is empty."""
        Letting.objects.all().delete()
        response = self.client.get(reverse('lettings:index'))
        self.assertContains(response, 'No lettings are available.')
        self.assertEqual(list(response.context['lettings_list']), [])

    @override_settings(DEBUG=False)
    def test_missing_letting_returns_404(self):
        """Return the custom 404 page when a letting ID does not exist."""
        response = self.client.get(reverse(
            'lettings:letting', kwargs={'letting_id': self.letting.pk + 100},
        ))
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, '404 - Page not found', status_code=404)

    def test_model_string_representations(self):
        """Use readable street and letting labels, including in the admin site."""
        self.assertEqual(str(self.address), '10 Main Street')
        self.assertEqual(str(self.letting), 'Holiday home')

    def test_address_validation(self):
        """Accept a valid address and reject values outside the declared limits."""
        self.address.full_clean()
        for field, value in [
            ('number', 10000), ('zip_code', 100000),
            ('state', 'C'), ('country_iso_code', 'US'), ('street', 'a' * 65),
        ]:
            with self.subTest(field=field, value=value):
                address = Address.objects.get(pk=self.address.pk)
                setattr(address, field, value)
                with self.assertRaises(ValidationError):
                    address.full_clean()

    def test_address_cannot_have_two_lettings(self):
        """Reject a second letting referring to an already associated address."""
        duplicate = Letting(title='Another home', address=self.address)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_deleting_address_removes_letting(self):
        """Preserve the cascade from an address to its associated letting."""
        self.address.delete()
        self.assertFalse(Letting.objects.filter(pk=self.letting.pk).exists())

    def test_admin(self):
        """Keep addresses and lettings editable through the admin site."""
        admin = User.objects.create_superuser('admin-test', 'admin@example.com', 'password')
        self.client.force_login(admin)
        for model, instance in [('address', self.address), ('letting', self.letting)]:
            response = self.client.get(reverse('admin:lettings_{}_changelist'.format(model)))
            self.assertEqual(response.status_code, 200)
            response = self.client.get(reverse(
                'admin:lettings_{}_change'.format(model), args=[instance.pk],
            ))
            self.assertEqual(response.status_code, 200)

    def test_admin_model_plurals(self):
        """Display Addresses and Lettings with the correct plurals in the admin."""
        admin = User.objects.create_superuser('plural-test', 'admin@example.com', 'password')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, 'Addresses')
        self.assertContains(response, 'Lettings')
        self.assertNotContains(response, 'Addresss')
