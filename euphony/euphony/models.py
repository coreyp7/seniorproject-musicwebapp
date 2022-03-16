from django.db import models

class Song(models.Model):
	artist = models.TextField()
	duration_ms = models.FloatField()
	explicit = models.FloatField()
    	id = models.TextField(primary_key=True)
    	name = models.TextField()
    	release_date = models.IntegerField()
    	year = models.IntegerField()
