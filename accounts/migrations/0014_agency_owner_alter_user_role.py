# Generated by Django 5.1.2 on 2024-11-10 00:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_profile_monthly_view_count_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="agency",
            name="owner",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owned_agency",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("staff", "Staff"),
                    ("agency_manager", "Agency Manager"),
                    ("agency_owner", "Agency Owner"),
                ],
                default="staff",
                max_length=20,
            ),
        ),
    ]
