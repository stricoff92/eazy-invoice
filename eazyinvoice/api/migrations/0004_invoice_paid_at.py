# Generated by Django 4.0.1 on 2022-01-31 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_invoice_is_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='paid_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]