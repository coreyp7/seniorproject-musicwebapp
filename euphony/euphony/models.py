from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
	artist = models.TextField()
	duration_ms = models.FloatField()
	explicit = models.FloatField()
	id = models.TextField(primary_key=True)
	name = models.TextField()
	release_date = models.IntegerField()
	year = models.IntegerField()

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist_name = models.CharField(max_length=200)
    songs = models.ManyToManyField(Song)
    