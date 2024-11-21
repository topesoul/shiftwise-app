# Generated by Django 5.1.2 on 2024-11-21 17:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0021_remove_agency_state_remove_profile_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agency",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owned_agencies",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]