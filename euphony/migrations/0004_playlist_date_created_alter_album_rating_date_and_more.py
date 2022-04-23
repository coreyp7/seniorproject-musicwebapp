# Generated by Django 4.0.3 on 2022-04-22 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('euphony', '0003_playlist_allow_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='date_created',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='album_rating',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='album_rating',
            name='rating_type',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='playlist_rating',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='playlist_rating',
            name='rating_type',
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name='song_rating',
            name='date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='song_rating',
            name='rating_type',
            field=models.BooleanField(null=True),
        ),
    ]
