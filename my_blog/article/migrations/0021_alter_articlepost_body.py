# Generated by Django 3.2.8 on 2021-11-14 14:15

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0020_remove_event_create_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlepost',
            name='body',
            field=ckeditor.fields.RichTextField(),
        ),
    ]
