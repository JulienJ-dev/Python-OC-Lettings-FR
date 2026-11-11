"""Regression checks for the home page and the migration of existing data."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
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
