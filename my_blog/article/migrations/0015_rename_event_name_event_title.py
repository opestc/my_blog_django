# Generated by Django 3.2.8 on 2021-11-08 14:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0014_rename_events_event'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='event_name',
            new_name='title',
        ),
    ]
