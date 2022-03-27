from django.urls import path
from . import views  # get views.py from current directory

urlpatterns = [
    path("", views.home, name="home"),
    path("account_link", views.link_account, name="link_account"),
    path("search_song", views.search_song, name="search_song"),
    path("search_song_results", views.search_song_results, name="search_song_results"),
    path('settings_general/', views.settings_general, name='settings_general'),
    path('settings_account/', views.settings_account, name='settings_account'),
    path('settings_security/', views.settings_security, name='settings_security'),

]
