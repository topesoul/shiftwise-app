from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0005_agency'),
    ]

    operations = [
        # Alter the verbose name for 'Agency' model
        migrations.AlterModelOptions(
            name='agency',
            options={'verbose_name_plural': 'Agencies'},
        ),
        # Add the ForeignKey to 'Shift' model
        migrations.AddField(
            model_name='shift',
            name='agency',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='shifts.agency'),
        ),
    ]
