from django.db import models
from django.contrib.auth.models import User

# NOTE: This table still needs a field for 'album_id'. Also import if necessary (should be in this file anyway)
class Song(models.Model):
	artist = models.TextField()
	duration_ms = models.FloatField()
	explicit = models.FloatField()
	id = models.TextField(primary_key=True)
	name = models.TextField()
	release_date = models.IntegerField()
	year = models.IntegerField()

# Section dedicated towards each rating table for songs/albums/playlists.
# NOTE: Include imports for Album and Playlist when those tables exist.

class Song_rating:
    id = models.TextField(primary_key=True) # unique ID of this rating
    user_id = models.ManyToManyField(User) # ID of user who left this rating
    song_id = models.ManyToManyField(Song) # ID of song which this rating corresponds to
    rating_type = models.BooleanField() # True = Upvote, False = Downvote

class album_rating:
    id = models.TextField(primary_key=True) # unique ID of this rating
    user_id = models.ManyToManyField(User) # ID of user who left this rating
    song_id = models.ManyToManyField(Album) # ID of album which this rating corresponds to
    rating_type = models.BooleanField() # True = Upvote, False = Downvote

class playlist_rating:
    id = models.TextField(primary_key=True) # unique ID of this rating
    user_id = models.ManyToManyField(User) # ID of user who left this rating
    playlist_id = models.ManyToManyField(Playlist) # ID of playlist which this rating corresponds to
    rating_type = models.BooleanField() # True = Upvote, False = Downvote
