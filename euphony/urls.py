from django.urls import path
from . import views  # get views.py from current directory

urlpatterns = [
    path("", views.home, name="home"),
    path("account_link", views.link_account, name="link_account"),
    path('profile/', views.profile, name='profile'),
    path('search_user/', views.search_user, name='search_users'),
]
