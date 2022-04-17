from unicodedata import name
from django.urls import include, path
from . import views  # get views.py from current directory

urlpatterns = [
    # Top section are the pages which the user can "officially click on" to access.
    path("", views.home, name="home"),
    path('dash', views.dash, name='dash'),
    path("link_account", views.link_account, name="link_account"),
    path("playlists/", views.allplaylists_view, name="playlists"),
    path('settings_general/', views.settings_general, name='settings_general'),
    path("search", views.search, name="search"),
    # Bottom section are pages which we redirect the user to.
    # Extensions of the pages above. (hope that makes sense)
    path("search_results", views.search_results, name="search_results"),
    path("create_playlist", views.create_playlist, name="create_playlist"),
    path('delete_playlist/<list_id>', views.delete_playlist, name='delete_playlist'),
    path('addsongs_view/<list_id>', views.addsongs_view, name='addsongs_view'),
    path('album_info/<id>', views.album_info, name='album_info'),
    path('songinfo/<music_id>', views.songinfo, name='songinfo'),
    path('comments/', include('django_comments_xtd.urls')),
    path('settings_account/', views.settings_account, name='settings_account'),
    path('settings_security/', views.settings_security, name='settings_security'),
    path('settings_reset_password/', views.settings_reset_password, name='settings_reset_password'),
    path('profile/', views.profile, name='profile'),
    #path('search_user/', views.search_user, name='search_users'),
    #path('search_user/<user_id>', views.search_userId, name='search_usersid'),
    path('topchart/', views.topChart, name="top"),
    path('topchart/<region_name>', views.topChart_post, name="top_selected"),
    path('proccess_vote/', views.proccess_vote, name="vote"),
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('playlist_song/<list_id>',views.playlist_song,name='playlist_song'),
    path('playlist_song/playlist_song_results/<list_id>',views.playlist_song_results,name='playlist_song_results'),
    path('playlist_song/playlist_song_results/add_song/<list_id>/<song_id>',views.add_song,name='add_song'),
    path('search_users/', views.search_users, name="search_users"),
    path('events/list_users/', views.list_users, name="list-users"),
    path('show_user/<user_id>', views.show_user, name="show_user"),
    path('friendship/', include('friendship.urls')),
    path('addFriend/<user_id>', views.addFriend, name="add_friend"),
    path('deleteFriend/<user_id>', views.deleteFriend, name="delete_friend"),
    #path('show_user/<user_id>', views.deleteFriend, name="delete_friend"),
    path('save_playlist/<list_id>', views.save_playlist, name='save_playlist'),
]
