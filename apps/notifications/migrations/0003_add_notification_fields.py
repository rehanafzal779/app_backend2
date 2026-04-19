# Generated migration for adding notification fields
# Run: python manage.py migrate notifications

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_delete_offlinesyncqueue_alter_notification_options'),
    ]

    operations = [
        # Add new fields to notifications table
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='status',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='expires_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='task_number',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='accepted_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='report_id',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]

