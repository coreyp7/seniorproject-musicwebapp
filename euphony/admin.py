from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(Song_rating)
admin.site.register(Album_rating)
admin.site.register(Playlist_rating)
admin.site.register(UserToken)
admin.site.register(User_Setting_Ext)