# Generated by Django 5.1.2 on 2024-11-10 20:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shifts", "0008_shiftassignment_attendance_status"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StaffPerformance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "wellness_score",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Score between 0 and 100",
                        max_digits=5,
                    ),
                ),
                (
                    "performance_rating",
                    models.DecimalField(
                        decimal_places=1, help_text="Rating out of 5", max_digits=3
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Excellent", "Excellent"),
                            ("Good", "Good"),
                            ("Average", "Average"),
                            ("Poor", "Poor"),
                        ],
                        default="Average",
                        max_length=10,
                    ),
                ),
                ("comments", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "shift",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performances",
                        to="shifts.shift",
                    ),
                ),
                (
                    "worker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="performances",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Staff Performance",
                "verbose_name_plural": "Staff Performances",
                "unique_together": {("worker", "shift")},
            },
        ),
    ]