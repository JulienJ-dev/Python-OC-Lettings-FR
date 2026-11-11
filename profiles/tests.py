"""Regression checks for profile pages, routes and administration."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from . import views
from .models import Profile


class ProfilesTests(TestCase):
    """Keep the existing profile features available after the move."""

    @classmethod
    def setUpTestData(cls):
        """Create a user and a profile in the new application."""
        cls.user = User.objects.create_user(
            username='jane', first_name='Jane', last_name='Doe', email='jane@example.com',
        )
        cls.profile = Profile.objects.create(user=cls.user, favorite_city='Irvine')

    def test_namespaced_routes(self):
        """Preserve public paths and route them to the new views."""
        self.assertEqual(reverse('profiles:index'), '/profiles/')
        detail = reverse('profiles:profile', kwargs={'username': self.user.username})
        self.assertEqual(detail, '/profiles/jane/')
        self.assertEqual(resolve('/profiles/').func, views.index)
        self.assertEqual(resolve(detail).func, views.profile)

    def test_index(self):
        """Display the existing list using the application template."""
        response = self.client.get(reverse('profiles:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/index.html')
        self.assertContains(response, self.user.username)
        self.assertContains(response, reverse(
            'profiles:profile', kwargs={'username': self.user.username},
        ))

    def test_detail(self):
        """Display the profile and its related user information."""
        response = self.client.get(reverse(
            'profiles:profile', kwargs={'username': self.user.username},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/profile.html')
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.profile.favorite_city)

    def test_admin(self):
        """Keep profiles editable through the admin site."""
        admin = User.objects.create_superuser('admin-test', 'admin@example.com', 'password')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:profiles_profile_changelist'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse(
            'admin:profiles_profile_change', args=[self.profile.pk],
        ))
        self.assertEqual(response.status_code, 200)
