# Generated by Django 5.1.2 on 2024-11-18 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0017_alter_user_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agency",
            name="agency_code",
            field=models.CharField(editable=False, max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name="agency",
            name="agency_type",
            field=models.CharField(
                choices=[
                    ("staffing", "Staffing"),
                    ("healthcare", "Healthcare"),
                    ("training", "Training"),
                    ("education", "Education"),
                    ("other", "Other"),
                ],
                default="staffing",
                max_length=100,
            ),
        ),
    ]
