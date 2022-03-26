from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from numpy.random import default_rng
import json

from .cashe_handler import DatabaseTokenHandler
from .forms import SongForm

scope = "user-library-read"
#sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

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
        #print(json.dumps(songs_json, indent=4, sort_keys=True))

        # Now we need to just take the information we need in the json and create a new dictionary.
        # The things we need are:
        # EVERYTHING LISTED IS IN "tracks":"items". An array of json objects.
        # "id" -> the spotify specific id for this song
        # "name" -> the name of the song
        # "track_number" -> (NOTE) The placement of this song in its album
        # "href" -> not sure, seems useful
        # "explicit" -> true/false for track
        # "album":"id" -> track's album id
        # "artists":"name" -> artist name on track
        # "album":"artists" -> list of artists
        # "album":"name" -> album name
        # "album":"release_date" -> album release date
        # There is also a "href" in every track object that is a link to the query.
        # Whatever that means.

        # JUST FOR NOW
        songs_json = songs_json["tracks"]
        songs_json = songs_json["items"]
        songs_json = songs_json[0]

        track_id = songs_json["id"]
        track_name = songs_json["name"]
        track_number = songs_json["track_number"] # track's placement in album
        track_explicit = songs_json["explicit"] # track's explicitity
        album_json = songs_json["album"] # album json object
        album_id = album_json["id"] # track's album id
        album_name = album_json["name"] # track's album name
        album_release_date = album_json["release_date"] # track's release date
        album_artists = album_json["artists"]

        track_info = {
            "id" : track_id,
            "track_name" : track_name,
            "track_number" : track_number,
            "track_explicit" : track_explicit,
            "album_id" : album_id
        }
        album_info = {
            "id" : album_id,
            "name" : album_name,
            "release_date" : album_release_date,
            "artists" : album_artists
        }
        print(f"Track info: {track_info}")
        print(f"Album info: {album_info}")
        pass
    else:
        print("unsuccessful :(")

    return render(request, "search_song.html", {"form_info": form, "songs": songs_json})
