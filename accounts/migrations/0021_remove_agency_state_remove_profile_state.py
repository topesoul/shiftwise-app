# Generated by Django 5.1.2 on 2024-11-21 04:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0020_alter_agency_country_alter_profile_country"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="agency",
            name="state",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="state",
        ),
    ]
