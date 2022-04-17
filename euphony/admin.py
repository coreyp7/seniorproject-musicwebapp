from django.contrib import admin

from .models import *
#from .models import Playlist, Song

# Register your models here.

#admin.site.register(Playlist)
#admin.site.register(Song)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'allow_comments')
    fieldsets = ((None,
                  {'fields': ('name',
                              'allow_comments', 'id',)}),)


admin.site.register(Song, CommentAdmin)

# Register your models here.
admin.site.register(Album)
#admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(Song_rating)
admin.site.register(Album_rating)
admin.site.register(Playlist_rating)
admin.site.register(UserToken)
admin.site.register(User_Setting_Ext)
admin.site.register(User_Profile)

