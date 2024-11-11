from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_profile_country"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE accounts_profile DROP COLUMN IF EXISTS travel_radius;",
            reverse_sql="ALTER TABLE accounts_profile ADD COLUMN travel_radius INTEGER NOT NULL DEFAULT 0;",
        ),
    ]
