# Generated by Django 5.1.2 on 2024-10-28 12:17

from django.db import migrations, models

import shifts.validators


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="shift",
            options={
                "ordering": ["shift_date", "start_time"],
                "verbose_name": "Shift",
                "verbose_name_plural": "Shifts",
            },
        ),
        migrations.AlterModelOptions(
            name="shiftassignment",
            options={
                "ordering": ["-assigned_at"],
                "verbose_name": "Shift Assignment",
                "verbose_name_plural": "Shift Assignments",
            },
        ),
        migrations.AlterField(
            model_name="shift",
            name="signature",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="signatures/",
                validators=[shifts.validators.validate_image],
            ),
        ),
    ]
