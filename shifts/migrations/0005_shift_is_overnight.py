# Generated by Django 5.1.2 on 2024-11-02 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0004_shiftassignment_completion_latitude_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="shift",
            name="is_overnight",
            field=models.BooleanField(
                default=False,
                help_text="Check this box if the shift spans into the next day.",
            ),
        ),
    ]
