from django.db import migrations, models


def copy_existing_project_people(apps, schema_editor):
    Person = apps.get_model('app01', 'Person')
    for person in Person.objects.exclude(ID_Project_id__isnull=True):
        project = person.ID_Project
        if project is not None:
            project.ID_Person.add(person)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0022_rename_user_legacyuser_alter_legacyuser_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='ID_Person',
            field=models.ManyToManyField(blank=True, related_name='projects', to='app01.person'),
        ),
        migrations.RunPython(copy_existing_project_people, noop_reverse),
    ]
