# Generated by Django 5.0.11 on 2025-02-14 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='is_group',
            field=models.BooleanField(default=False),
        ),
    ]
