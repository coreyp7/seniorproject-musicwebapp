from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from numpy.random import default_rng, shuffle
import json

from .cashe_handler import DatabaseTokenHandler
from .spotify_queries import *

from .forms import SongForm

from .models import Song

scope = "user-library-read"
#sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

def home(request):
    return render(request, "home.html", {})


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

def dash(request):

    id_list = []

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):

        temp_client = gen_client(user, scope)
        id_list = gen_recomendations(temp_client)
        id_list = get_song_id_list(temp_client, id_list)
        shuffle(id_list)# todo actually sort the ids by rank at some point
    return render(request, 'dash.html', {'recommendations' : id_list[:50]})

# Search song page that is blank, what is initially shown to user.
@require_GET
def search_song(request):
    form = SongForm()
    return render(request, "search_song.html", {"form": form})

# Search song page that is displaying any results that the user requested
# on the search_song page.
@require_POST
def search_song_results(request):
    form = SongForm(request.POST)

    if form.is_valid():
        # find song list from spotipy and return the list in the form of a parameter in our render
        track_query = "track:"+form.cleaned_data["song_name"]
        songs_json = sp.search(track_query) # json with song information
        #songs = json.load(songs_json)
        #tracks = songs_json["tracks"]
        print(json.dumps(songs_json, indent=4, sort_keys=True))

        # Now we need to just take the information we need in the json and create a new dictionary.
        # The things we need are:
        # I THINK ALL OF THESE ARE IN "items".
        # "id" -> the spotify specific id for this song
        # "name" -> the name of the song
        # "track_number" -> the placement of this song in its album
        # "href" -> not sure, seems useful
        # "explicit" -> true/false
        # "artists":"name" -> artist name
        # "album":"name" -> album name
        # "album":"release_date" -> album release date
        # "album":"id" -> album id
        # There is also a "href" in every track object that is a link to the query.
        # Whatever that means.
        pass
    else:
        print("unsuccessful :(")

    return render(request, "search_song.html", {"form_info": form, "songs": songs_json})
