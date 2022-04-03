# Generated by Django 4.0.3 on 2022-04-02 20:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('euphony', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='album_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='euphony.album'),
        ),
        migrations.AlterField(
            model_name='user_setting_ext',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='userExt', to=settings.AUTH_USER_MODEL),
        ),
    ]
