# Generated by Django 5.1.2 on 2024-11-02 18:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_alter_user_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invitation",
            name="agency",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="accounts.agency",
            ),
        ),
    ]
