# Generated by Django 5.1.2 on 2024-11-20 16:58

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0015_alter_shiftassignment_attendance_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shift",
            name="end_date",
            field=models.DateField(
                default=django.utils.timezone.now,
                help_text="Specify the date when the shift ends.",
            ),
            preserve_default=False,
        ),
    ]