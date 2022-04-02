from unicodedata import name
from django.urls import include, path
from . import views  # get views.py from current directory

urlpatterns = [
    # Top section are the pages which the user can "officially click on" to access.
    path("", views.home, name="home"),
    path('dash', views.dash, name='dash'),
    path("link_account", views.link_account, name="link_account"),
    path("search_song", views.search_song, name="search_song"),
    path("search_album", views.search_album, name="search_album"),
    path("playlists", views.allplaylists_view, name="playlists" ),
    path('settings_general/', views.settings_general, name='settings_general'),
    # Bottom section are pages which we redirect the user to.
    # Extensions of the pages above. (hope that makes sense)
    path("search_song_results", views.search_song_results, name="search_song_results"),
    path("search_album_results", views.search_album_results, name="search_album_results"),
    path("create_playlist", views.create_playlist, name="create_playlist"),
    path('delete_playlist/<list_id>', views.delete_playlist, name='delete_playlist'),
    path('addsongs_view', views.addsongs_view, name='addsongs_view'),
    path('album_info/<id>', views.album_info, name='album_info'),
    path('songinfo/<music_id>', views.songinfo, name='songinfo'),
    path('comments/', include('django_comments_xtd.urls')),
    path('settings_account/', views.settings_account, name='settings_account'),
    path('settings_security/', views.settings_security, name='settings_security'),
    path('profile/', views.profile, name='profile'),
    path('search_user/', views.search_user, name='search_users'),
    path('topchart/', views.topChart, name="top"),
    path('proccess_vote/', views.proccess_vote, name="vote"),
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
]
