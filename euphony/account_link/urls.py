from django.urls import path
from . import views

urlpatterns = [
    path('', views.link_account, name='link_account'),
]
