from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_booking_abandoned_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='booking_reference',
            field=models.CharField(blank=True, default='', editable=False, max_length=12, null=True),
        ),
    ]
