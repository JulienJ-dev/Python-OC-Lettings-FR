"""Regression checks for profile pages, routes and administration."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
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

    def test_empty_index(self):
        """Explain that no profiles are available when the list is empty."""
        Profile.objects.all().delete()
        response = self.client.get(reverse('profiles:index'))
        self.assertContains(response, 'No profiles are available.')
        self.assertEqual(list(response.context['profiles_list']), [])

    @override_settings(DEBUG=False)
    def test_missing_profile_returns_404(self):
        """Return the custom 404 page for an unknown username."""
        response = self.client.get(reverse(
            'profiles:profile', kwargs={'username': 'missing-user'},
        ))
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, '404 - Page not found', status_code=404)

    @override_settings(DEBUG=False)
    def test_user_without_profile_returns_404(self):
        """Return 404 when the user exists but has no associated profile."""
        self.profile.delete()
        response = self.client.get(reverse(
            'profiles:profile', kwargs={'username': self.user.username},
        ))
        self.assertContains(response, '404 - Page not found', status_code=404)

    def test_model_string_representation(self):
        """Use the username as the profile's readable label."""
        self.assertEqual(str(self.profile), 'jane')

    def test_favorite_city_is_optional(self):
        """Accept an empty favorite city when validating a profile."""
        self.profile.favorite_city = ''
        self.profile.full_clean()

    def test_favorite_city_length_is_limited(self):
        """Reject a favorite city longer than the declared 64 characters."""
        self.profile.favorite_city = 'a' * 65
        with self.assertRaises(ValidationError):
            self.profile.full_clean()

    def test_user_cannot_have_two_profiles(self):
        """Reject a second profile associated with the same user."""
        with self.assertRaises(ValidationError):
            Profile(user=self.user).full_clean()

    def test_deleting_user_removes_profile(self):
        """Preserve the cascade from a user to the associated profile."""
        self.user.delete()
        self.assertFalse(Profile.objects.filter(pk=self.profile.pk).exists())

    def test_admin_model_plural(self):
        """Display Profiles with the correct plural in the administration site."""
        admin = User.objects.create_superuser('plural-test', 'admin@example.com', 'password')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, 'Profiles')
