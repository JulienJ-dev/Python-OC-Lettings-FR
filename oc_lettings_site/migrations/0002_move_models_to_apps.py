"""Copy existing data to the new applications before removing the old tables."""

from django.db import migrations


def copy_to_new_apps(apps, schema_editor):
    """Copy records to the new applications, preserving keys and relations.

    Args:
        apps (StateApps): Historical models at this point in the migration history.
        schema_editor (BaseDatabaseSchemaEditor): Access to the active database alias.

    Returns:
        None: Records are written to the new application's tables.
    """
    database = schema_editor.connection.alias
    for app_label, model_name in [
        ('lettings', 'Address'), ('lettings', 'Letting'), ('profiles', 'Profile'),
    ]:
        old_model = apps.get_model('oc_lettings_site', model_name)
        new_model = apps.get_model(app_label, model_name)
        new_model.objects.using(database).bulk_create([
            new_model(**fields) for fields in old_model.objects.using(database).values()
        ])


def restore_old_models(apps, schema_editor):
    """Restore records after Django recreates the old tables during a rollback.

    Args:
        apps (StateApps): Historical models at this point in the migration history.
        schema_editor (BaseDatabaseSchemaEditor): Access to the active database alias.

    Returns:
        None: Records are restored and the new tables are emptied for reapplication.
    """
    database = schema_editor.connection.alias
    for app_label, model_name in [
        ('lettings', 'Address'), ('lettings', 'Letting'), ('profiles', 'Profile'),
    ]:
        old_model = apps.get_model('oc_lettings_site', model_name)
        new_model = apps.get_model(app_label, model_name)
        old_model.objects.using(database).bulk_create([
            old_model(**fields) for fields in new_model.objects.using(database).values()
        ])
    # Clear dependent rows first so the migration can be applied again after a rollback.
    for app_label, model_name in [
        ('lettings', 'Letting'), ('lettings', 'Address'), ('profiles', 'Profile'),
    ]:
        apps.get_model(app_label, model_name).objects.using(database).all().delete()


class Migration(migrations.Migration):
    """Create new tables first, copy data, and then remove the original models."""

    dependencies = [
        ('oc_lettings_site', '0001_initial'),
        ('lettings', '0001_initial'),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_to_new_apps, restore_old_models),
        migrations.DeleteModel(
            name='Letting',
        ),
        migrations.DeleteModel(
            name='Address',
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
    ]
