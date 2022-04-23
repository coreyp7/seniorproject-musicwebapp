from django.contrib import admin

from .models import *
from django_comments_xtd.admin import XtdCommentsAdmin
#from .models import Playlist, Song

# Register your models here.

#admin.site.register(Playlist)
#admin.site.register(Song)

class CustomCommentAdmin(XtdCommentsAdmin):
    list_display = ('cid', 'name', 'object_pk',
                    'ip_address', 'submit_date', 'followup', 'is_public',
                    'is_removed')
    fieldsets = (
        (None, {'fields': ('content_type', 'object_pk', 'site')}),
        ('Content', {'fields': ('user', 'user_name', 'user_email',
                                'user_url', 'comment', 'followup')}),
        ('Metadata', {'fields': ('submit_date', 'ip_address',
                                 'is_public', 'is_removed')}),
    )



admin.site.register(CustomComment, CustomCommentAdmin)

# Register your models here.
admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(Song_rating)
admin.site.register(Album_rating)
admin.site.register(Playlist_rating)
admin.site.register(UserToken)
admin.site.register(User_Setting_Ext)
admin.site.register(User_Profile)

