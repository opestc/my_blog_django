# Generated by Django 3.2.8 on 2021-11-08 13:36

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0011_alter_banner_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Events',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_name', models.CharField(blank=True, max_length=255, null=True)),
                ('start_time', models.DateTimeField(default='')),
                ('end_time', models.DateTimeField(default='')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('description', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
    ]
