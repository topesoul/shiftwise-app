# Generated by Django 5.1.2 on 2024-11-04 21:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0004_subscription_billing_address_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="plan",
            name="price_yearly",
        ),
    ]
