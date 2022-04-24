
from operator import truediv
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.urls import reverse
import json
import re

from django_comments_xtd.forms import XtdCommentForm
from django_comments_xtd.models import TmpXtdComment
from datetime import datetime
from django_comments_xtd.models import XtdComment


class Album(models.Model):
    artists = models.TextField()
    id = models.TextField(primary_key=True)  # Spotify ID of album
    name = models.TextField()
    release_date = models.TextField()
    cover = models.URLField(max_length=200) # link to cover of album
    total_tracks = models.IntegerField()
    allow_comments = models.BooleanField('allow comments', default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('album_info', args=[str(self.id)])

class Song(models.Model):
    id = models.TextField(primary_key=True)  # Spotify ID of song
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE)
    name = models.TextField()
    artists = models.TextField()
    duration_ms = models.FloatField()
    explicit = models.FloatField()
    release_date = models.TextField()
    track_number = models.IntegerField()
    disc = models.IntegerField()
    allow_comments = models.BooleanField('allow comments', default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('songinfo', args=[str(self.id)])


class Playlist(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(max_length=200)
    songs = models.ManyToManyField(Song)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    allow_comments = models.BooleanField('allow comments', default=True)
    date_created = models.DateField(null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('addsongs_view', args=[str(self.id)])


class CustomComment(XtdComment):
    def save(self, *args, **kwargs):
        if self.user:
            self.user_name = self.user.display_name
        super(CustomComment, self).save(*args, **kwargs)

# Section dedicated towards each rating table for songs/albums/playlists.


class Song_rating(models.Model):
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None
    )  # ID of user who left this rating
    song_id = models.ForeignKey(
        Song, on_delete=models.CASCADE, default=None
    )  # ID of song which this rating corresponds to
    rating_type = models.BooleanField(null=True)  # True = Upvote, False = Downvote
    date = models.DateTimeField(default=datetime.now, null=True) # date that the rating was given. Helpful for getting most recent feed


class Album_rating(models.Model):
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None
    )  # ID of user who left this rating
    album_id = models.ForeignKey(
        Album, on_delete=models.CASCADE, default=None
    )  # ID of album which this rating corresponds to
    rating_type = models.BooleanField(null=True)  # True = Upvote, False = Downvote
    date = models.DateTimeField(default=datetime.now, null=True)     # date that the rating was given. Helpful for getting most recent feed


class Playlist_rating(models.Model):
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, default=None
    )  # ID of user who left this rating
    playlist_id = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, default=None
    )  # ID of playlist which this rating corresponds to
    rating_type = models.BooleanField(null=True)  # True = Upvote, False = Downvote
    date = models.DateTimeField(default=datetime.now, null=True)  # date that the rating was given. Helpful for getting most recent feed

# User relevant tables

class UserToken(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    token = models.TextField()

class User_Setting_Ext(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userExt')
    dark_mode = models.BooleanField(default=False) #Color mode: dark/white toggle
    explicit = models.BooleanField(default=False) #Explicit content toggle

class User_Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    saved_playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE) 