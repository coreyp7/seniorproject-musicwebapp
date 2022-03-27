from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from euphony.models import Playlist
from .forms import PlaylistForm
from django.contrib import messages


import spotipy

from .cashe_handler import DatabaseTokenHandler
from numpy.random import default_rng


def home(request):
    return render(request, "home.html", {})


scope = "user-library-read"


def link_account(request):

    if str(request.user) != "AnonymousUser" and (
        user := User.objects.get(pk=int(request.user.id))
    ):

        cache_handler = DatabaseTokenHandler(user)
        auth_manager = spotipy.oauth2.SpotifyOAuth(
            scope=scope, cache_handler=cache_handler
        )

        if request.GET.get("code"):
            token = auth_manager.parse_response_code(request.build_absolute_uri())
            token_info = auth_manager.get_access_token(token)
            cache_handler.save_token_to_cache(token_info)
            return redirect("/")

        elif not auth_manager.validate_token(cache_handler.get_cached_token()):
            auth_url = auth_manager.get_authorize_url()
            return redirect(auth_url)

    return redirect("/")

def allplaylists_view(request):
    playlists=Playlist.objects.all()
    return render(request,'playlists.html',{'playlists': playlists})

def create_playlist(request):
    submitted = False
    if request.method == "POST":
        form = PlaylistForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, ('New Playlist Created!'))
            return redirect('playlists')
    else:
        form = PlaylistForm
        if 'submitted' in request.GET:
            submitted = True
        return render(request,'createplaylist.html',{'form': form, 'submitted': submitted})

def delete_playlist(request, list_id):
    item = Playlist.objects.get(pk=list_id)
    item.delete()
    messages.success(request, ('Playlist Has Been Deleted!'))
    return redirect('playlists')

def addsongs_view(request):
    return render(request, "addsongs.html", {})

