# Generated by Django 3.2.25 on 2024-09-29 10:32

from django.db import migrations, models

def populate_shift_fields(apps, schema_editor):
    Shift = apps.get_model('shifts', 'Shift')
    default_values = {
        'address_line1': 'Unknown Address',
        'city': 'Unknown City',
        'name': 'Unnamed Shift',
        'start_time': '09:00',  # Default start time
        'end_time': '17:00',    # Default end time
        'shift_date': '2000-01-01',  # Placeholder date
        'postcode': '00000',
    }
    for field, default in default_values.items():
        filter_kwargs = {f"{field}__isnull": True}
        update_kwargs = {field: default}
        Shift.objects.filter(**filter_kwargs).update(**update_kwargs)

class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0002_auto_20240928_1504'),
    ]

    operations = [
        migrations.RunPython(populate_shift_fields),
        migrations.AlterField(
            model_name='shift',
            name='address_line1',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='shift',
            name='city',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='shift',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='shift',
            name='start_time',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='shift',
            name='end_time',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='shift',
            name='shift_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='shift',
            name='postcode',
            field=models.CharField(max_length=10),
        ),
    ]