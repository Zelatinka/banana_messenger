# Generated by Django 5.1.6 on 2025-03-05 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0003_auto_20250305_0906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='message',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
