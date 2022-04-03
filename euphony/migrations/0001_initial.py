
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('artist', models.TextField()),
                ('id', models.TextField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('release_date', models.TextField()),
                ('cover', models.URLField()),
                ('total_tracks', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.TextField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.TextField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('artist', models.TextField()),
                ('duration_ms', models.FloatField()),
                ('explicit', models.FloatField()),
                ('release_date', models.TextField()),
                ('track_number', models.IntegerField()),
                ('disc', models.IntegerField()),
                ('allow_comments', models.BooleanField(default=True, verbose_name='allow comments')),
                ('album_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='euphony.album')),
            ],
        ),
        migrations.CreateModel(
            name='UserToken',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('token', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='User_Setting_Ext',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dark_mode', models.BooleanField(default=False)),
                ('explicit', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Song_rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_type', models.BooleanField()),
                ('date', models.TextField()),
                ('song_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='euphony.song')),
                ('user_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Playlist_rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_type', models.BooleanField()),
                ('date', models.TextField()),
                ('playlist_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='euphony.playlist')),
                ('user_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='playlist',
            name='songs',
            field=models.ManyToManyField(to='euphony.song'),
        ),
        migrations.AddField(
            model_name='playlist',
            name='user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Album_rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating_type', models.BooleanField()),
                ('date', models.TextField()),
                ('album_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='euphony.album')),
                ('user_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
