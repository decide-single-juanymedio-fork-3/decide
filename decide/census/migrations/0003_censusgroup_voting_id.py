# Generated by Django 4.1 on 2023-12-07 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('census', '0002_censusgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='censusgroup',
            name='voting_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
