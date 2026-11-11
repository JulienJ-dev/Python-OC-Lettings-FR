"""Regression checks for letting pages, routes and administration."""

from django.contrib.auth.models import User
from django.test import TestCase
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
