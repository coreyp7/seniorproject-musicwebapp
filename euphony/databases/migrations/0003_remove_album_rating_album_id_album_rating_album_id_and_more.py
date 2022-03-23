# Generated by Django 4.0.3 on 2022-03-21 15:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('databases', '0002_song_rating_playlist_rating_album_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='album_rating',
            name='album_id',
        ),
        migrations.AddField(
            model_name='album_rating',
            name='album_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='databases.album'),
        ),
        migrations.RemoveField(
            model_name='album_rating',
            name='user_id',
        ),
        migrations.AddField(
            model_name='album_rating',
            name='user_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='playlist_rating',
            name='playlist_id',
        ),
        migrations.AddField(
            model_name='playlist_rating',
            name='playlist_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='databases.playlist'),
        ),
        migrations.RemoveField(
            model_name='playlist_rating',
            name='user_id',
        ),
        migrations.AddField(
            model_name='playlist_rating',
            name='user_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='song_rating',
            name='song_id',
        ),
        migrations.AddField(
            model_name='song_rating',
            name='song_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='databases.song'),
        ),
        migrations.RemoveField(
            model_name='song_rating',
            name='user_id',
        ),
        migrations.AddField(
            model_name='song_rating',
            name='user_id',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
