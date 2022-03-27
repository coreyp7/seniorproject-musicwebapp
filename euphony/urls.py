from unicodedata import name
from django.urls import path
from . import views  # get views.py from current directory

urlpatterns = [
    path("", views.home, name="home"),
    path("account_link", views.link_account, name="link_account"),
    path("playlists", views.allplaylists_view, name="playlists" ),
    path("create_playlist", views.create_playlist, name="create_playlist"),
    path('delete_playlist/<list_id>', views.delete_playlist, name='delete_playlist'),
    path('addsongs_view', views.addsongs_view, name='addsongs_view'),
]
