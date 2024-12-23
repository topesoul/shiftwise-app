# Generated by Django 5.1.2 on 2024-11-13 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0009_staffperformance"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shift",
            name="end_date",
            field=models.DateField(
                blank=True, help_text="Specify the date when the shift ends.", null=True
            ),
        ),
    ]
