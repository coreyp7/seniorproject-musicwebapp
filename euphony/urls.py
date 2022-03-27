from django.urls import path
from . import views  # get views.py from current directory

urlpatterns = [
    path("", views.home, name="home"),
    path("account_link", views.link_account, name="link_account"),
    path("search_song", views.search_song, name="search_song"),
    path("search_song_results", views.search_song_results, name="search_song_results"),
    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('topchart/', views.topChart, name="top"),
]
