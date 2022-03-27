from django.db import models

# Create your models here.
from django.contrib.auth.models import User


class Album(models.Model):
    artist = models.TextField()  # Just artist name, not an ID or anything
    duration = models.FloatField()  # Length of album
    explicit = models.FloatField()
    id = models.TextField(primary_key=True)  # Spotify ID of album
    name = models.TextField()
    release_date = models.TextField()


class Song(models.Model):
    id = models.TextField(primary_key=True)  # Spotify ID of song
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE)
    name = models.TextField()
    artist = models.TextField()
    duration_ms = models.FloatField()
    explicit = models.FloatField()
    release_date = models.TextField()


class Playlist(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(max_length=200)
    songs = models.ManyToManyField(Song)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)


# Section dedicated towards each rating table for songs/albums/playlists.


class Song_rating(models.Model):
    id = models.TextField(primary_key=True)  # unique ID of this rating
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None
    )  # ID of user who left this rating
    song_id = models.ForeignKey(
        Song, on_delete=models.CASCADE, default=None
    )  # ID of song which this rating corresponds to
    rating_type = models.BooleanField()  # True = Upvote, False = Downvote
    date = (
        models.TextField()
    )  # date that the rating was given. Helpful for getting most recent feed


class Album_rating(models.Model):
    id = models.TextField(primary_key=True)  # unique ID of this rating
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None
    )  # ID of user who left this rating
    album_id = models.ForeignKey(
        Album, on_delete=models.CASCADE, default=None
    )  # ID of album which this rating corresponds to
    rating_type = models.BooleanField()  # True = Upvote, False = Downvote
    date = (
        models.TextField()
    )  # date that the rating was given. Helpful for getting most recent feed


class Playlist_rating(models.Model):
    id = models.TextField(primary_key=True)  # unique ID of this rating
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None
    )  # ID of user who left this rating
    playlist_id = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, default=None
    )  # ID of playlist which this rating corresponds to
    rating_type = models.BooleanField()  # True = Upvote, False = Downvote
    date = (
        models.TextField()
    )  # date that the rating was given. Helpful for getting most recent feed

# User relevant tables

class UserToken(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    token = models.TextField()

class User_Setting_Ext(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	dark_mode = models.BooleanField(default=False) #Color mode: dark/white toggle
	explicit = models.BooleanField(default=False) #Explicit content toggle
	