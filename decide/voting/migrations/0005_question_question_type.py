# Generated by Django 4.1 on 2023-12-10 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0004_alter_voting_postproc_alter_voting_tally'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('MCQ', 'Multiple Choice'), ('YN', 'Yes/No')], default='MCQ', max_length=3),
        ),
    ]
