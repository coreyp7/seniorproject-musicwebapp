# Generated by Django 4.0.3 on 2022-03-28 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('euphony', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='allow_comments',
            field=models.BooleanField(default=True, verbose_name='allow comments'),
        ),
    ]
