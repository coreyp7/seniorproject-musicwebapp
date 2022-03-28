from django.contrib import admin
from .models import Song
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