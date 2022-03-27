from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse
from django.db.utils import OperationalError
from django.core.exceptions import ObjectDoesNotExist # for checking if row exists

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from numpy.random import default_rng, shuffle
import json

from .cashe_handler import DatabaseTokenHandler
from .spotify_queries import *

from .forms import SongForm
from .models import *

from .models import Song, UserToken

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

    '''
    returns a webapge of recommendations, or if an account is unlinked it returns "account not linked with spotify" 
    '''

    id_list = []

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):

        temp_client = gen_client(user, scope)
        if temp_client != None:
            id_list = gen_recomendations(temp_client)
            id_list = get_song_id_list(temp_client, id_list)
            shuffle(id_list)# todo actually sort the ids by rank at some point
        else:
            return HttpResponse("account not linked with spotify")

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

        final_songs_list = [] # list of dictionaries

        songs_json = songs_json["tracks"]
        for json_obj in songs_json["items"]:
            # track stuff
            track_id = json_obj["id"]
            track_name = json_obj["name"]
            track_number = json_obj["track_number"] # track's placement in album
            track_explicit = json_obj["explicit"] # track's explicitity
            track_artists = json_obj["artists"]
            track_artists_list = [] # list of track's artists formatted how we want
            for artist_obj in track_artists:
                artist_name = artist_obj["name"]
                track_artists_list.append(artist_name)
            # album stuff
            album_json = json_obj["album"] # album json object
            album_id = album_json["id"] # track's album id
            album_name = album_json["name"] # track's album name
            album_release_date = album_json["release_date"] # track's release date
            album_artists = album_json["artists"]
            album_artists_list = [] # list of track's artists formatted how we want
            for artist_obj in album_artists:
                artist_name = artist_obj["name"]
                album_artists_list.append(artist_name)
            #artist stuff

            track_info = {
                "id" : track_id,
                "name" : track_name,
                "number" : track_number,
                "explicit" : track_explicit,
                "artists" : track_artists_list,
                "album_id" : album_id,
                "album_name" : album_name,
                "album_release_date" : album_release_date,
                "album_artists" : album_artists_list,
            }
            # Now that track_info has been created, let's check if this
            # song exists.
            try:
                try:
                    song_exists = Song.objects.get(pk=track_info["id"])
                    if song_exists:
                        print("Already exists")
                except ObjectDoesNotExist:
                    new_song = Song()
                    new_song.id = track_info["id"]
                    new_song.album_id = None #TEMPORARY
                    new_song.name = track_info["name"]
                    new_song.artist = track_info["artists"][0] #TEMPORARY
                    new_song.duration_ms = 1 #TEMPORARY
                    new_song.explicit = False #TEMPORARY
                    new_song.release_date = track_info["album_release_date"]
                    new_song.track_number = 1 #TEMPORARY
                    new_song.save()
                    print(f"new song {track_info['name']} added to db!")
            except OperationalError:
                print("Song table doesn't exist.")
            
            #print(f"Track info: {json.dumps(track_info, indent=4)}")
            final_songs_list.append(track_info)

        return render(request, "search_song.html", 
        {"form_info": form, "songs": final_songs_list})
    else:
        print("unsuccessful :(")

    return render(request, "search_song.html", {"form_info": form, "songs": None})
