"""Test the home page, error pages and migration of existing data."""

from unittest.mock import patch

from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import reverse


class HomeTests(TestCase):
    """Keep the home page and its navigation working."""

    def test_home(self):
        """Render the application template with links to the two new namespaces."""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oc_lettings_site/index.html')
        self.assertContains(response, 'Welcome to Holiday Homes')
        self.assertContains(response, reverse('lettings:index'))
        self.assertContains(response, reverse('profiles:index'))


@override_settings(DEBUG=False)
class ErrorPageTests(SimpleTestCase):
    """Check Django's error handlers with production-style error responses."""

    def test_unknown_url_uses_custom_404(self):
        """Return the custom template and status 404 for an unknown route."""
        response = self.client.get('/unknown-page/')
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, '404 - Page not found', status_code=404)
        self.assertContains(response, 'Back to home', status_code=404)
        self.assertContains(response, 'href="{}"'.format(reverse('index')), status_code=404)

    def test_unexpected_error_uses_custom_500(self):
        """Render a real error response without exposing exception details."""
        with patch('oc_lettings_site.views.render', side_effect=RuntimeError('private failure')):
            response = Client(raise_request_exception=False).get('/')
        self.assertTemplateUsed(response, '500.html')
        self.assertContains(response, '500 - Server error', status_code=500)
        self.assertContains(response, 'Back to home', status_code=500)
        self.assertNotContains(response, 'private failure', status_code=500)
        self.assertNotContains(response, 'Traceback', status_code=500)

    def test_database_failure_uses_custom_500(self):
        """Keep the error page usable when the letting query fails."""
        with patch(
            'lettings.views.Letting.objects.all', side_effect=DatabaseError('private query'),
        ):
            response = Client(raise_request_exception=False).get(reverse('lettings:index'))
        self.assertTemplateUsed(response, '500.html')
        self.assertContains(response, '500 - Server error', status_code=500)
        self.assertNotContains(response, 'private query', status_code=500)


class ModelMigrationTests(TransactionTestCase):
    """Check that moving the models preserves records, IDs and relationships."""

    def test_move_models_and_rollback(self):
        """Migrate populated old tables, reverse the migration and apply it again."""
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        original = [('oc_lettings_site', '0001_initial')]
        try:
            executor.migrate([('lettings', None), ('profiles', None)])
            old_apps = executor.loader.project_state(original).apps
            user = old_apps.get_model('auth', 'User').objects.create(username='migration-user')
            old_apps.get_model('oc_lettings_site', 'Address').objects.create(
                id=42, number=10, street='Main Street', city='Irvine', state='CA',
                zip_code=92618, country_iso_code='USA',
            )
            old_apps.get_model('oc_lettings_site', 'Letting').objects.create(
                id=73, title='Migration home', address_id=42,
            )
            old_apps.get_model('oc_lettings_site', 'Profile').objects.create(
                id=98, user_id=user.pk, favorite_city='Irvine',
            )
            expected = {
                name: list(old_apps.get_model('oc_lettings_site', name).objects.values())
                for name in ['Address', 'Letting', 'Profile']
            }

            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            new_apps = executor.loader.project_state(latest).apps
            for app_label, name in [
                ('lettings', 'Address'), ('lettings', 'Letting'), ('profiles', 'Profile'),
            ]:
                model = new_apps.get_model(app_label, name)
                self.assertEqual(list(model.objects.values()), expected[name])
                self.assertNotIn(
                    'oc_lettings_site_' + name.lower(), connection.introspection.table_names(),
                )

            executor = MigrationExecutor(connection)
            executor.migrate(original)
            restored_apps = executor.loader.project_state(original).apps
            for name, records in expected.items():
                model = restored_apps.get_model('oc_lettings_site', name)
                self.assertEqual(list(model.objects.values()), records)

            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            new_apps = executor.loader.project_state(latest).apps
            for app_label, name in [
                ('lettings', 'Address'), ('lettings', 'Letting'), ('profiles', 'Profile'),
            ]:
                model = new_apps.get_model(app_label, name)
                self.assertEqual(list(model.objects.values()), expected[name])
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
