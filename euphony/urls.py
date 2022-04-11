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
    path('settings_reset_password/', views.settings_reset_password, name='settings_reset_password'),
    path('profile/', views.profile, name='profile'),
    path('search_user/', views.search_user, name='search_users'),
    path('topchart/', views.topChart, name="top"),

    path('topchart/Global', views.topChart_Global, name="Global"),
    path('topchart/Canada', views.topChart_Canada, name="Canada"),
    path('topchart/Japan', views.topChart_Japan, name="Japan"),
    path('topchart/Mexico', views.topChart_Mexico, name="Mexico"),
    path('topchart/USA', views.topChart_USA, name="USA"),

    path('proccess_vote/', views.proccess_vote, name="vote"),

    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),

    path('user_group_all/', views.ListGroups.as_view(), name='all'),
    path('user_group_create/', views.CreateGroup.as_view(), name='create'),
    path('user_group_page/<user_group_id>', views.SingleGroup.as_view(), name='single'),
    path('user_group_update/<user_group_id>', views.UpdateGroup.as_view(), name='update'),
    path('user_group_join/<user_group_id>', views.JoinGroup.as_view(), name='join'),
    path('user_group_leave/<user_group_id>', views.LeaveGroup.as_view(), name='leave'),

    url(r'^$', views.PostList.as_view(), name='all'),
    url(r'new/$', views.CreatePost.as_view(), name='create'),
    url(r'by/(?P<username>[-\w]+)/$', views.UserPosts.as_view(), name='for_user'),
    url(r'by/(?P<username>[-\w]+)/(?P<pk>\d+)/$', views.PostDetail.as_view(), name='single'),
    url(r'update/(?P<pk>\d+)/$', views.UpdatePost.as_view(), name='update'),
    url(r'delete/(?P<pk>\d+)/$', views.DeletePost.as_view(), name='delete'),
]
