from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse
from django.db.utils import OperationalError
from django.core.exceptions import ObjectDoesNotExist # for checking if row exists
from euphony.models import Playlist
from .forms import PlaylistForm
from django.contrib import messages
from friendship.models import Friend, Follow, Block
from django.contrib.auth import authenticate, login, logout

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from numpy.random import default_rng, shuffle
import json

from .cashe_handler import DatabaseTokenHandler
from .spotify_queries import *

from .forms import SongForm, CreateUserForm
from .models import *

from .models import Song, UserToken, Song_rating

from django.contrib import messages
from .forms import EditUserForm

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

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

def get_song_rating_numbers(song_list):

    '''
    takes in a list of song ids, and returns a list containing the number of votes for each song
    '''
    ratings_list = []

    for song in song_list:
        rating_list = Song_rating.objects.filter(song_id=song)

        rating = 0
        for item in list(rating_list):
            if(item.rating_type):
                rating += 1
            else:
                rating += -1

        ratings_list.append(rating)

    return ratings_list

def dash(request):

    '''
    returns a webapge of recommendations, or if an account is unlinked it returns "account not linked with spotify"
    '''

    id_list = []
    posts = []

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):

        temp_client = gen_client(user, scope)
        if temp_client != None:
            album_list = gen_recomendations(temp_client)
            song_list = get_song_list(temp_client, album_list)
            posts = [{ "song" : item[0] , "ratings" : item[1]} for item in zip(song_list, get_song_rating_numbers(song_list)) ]
            shuffle(posts)
            posts = posts[:50]
            posts.sort(key = lambda item : item['ratings'], reverse=True )
        else:
            return HttpResponse("account not linked with spotify")

    return render(request, 'dash.html', {'recommendations' : posts})


def proccess_vote(request):

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):
        song = Song.objects.get(id=request.POST['song'])
        rating = list(Song_rating.objects.filter(user_id=user, song_id=song))
        new_vote = (int(request.POST['vote']) == 1)
        if len(rating) == 0:
            vote = Song_rating.objects.create(song_id=song, user_id=user, rating_type=new_vote)
            print('new', vote.id, vote.song_id ,vote.rating_type)
            if(new_vote):
                return HttpResponse('1')
            else:
                return HttpResponse('-1')
        else:
            vote = rating[0]
            old_vote = vote.rating_type
            print('not new',vote.id, vote.song_id ,vote.rating_type)
            if(old_vote == new_vote):
                vote.delete()
                if(old_vote):
                    return HttpResponse(-1)
                else:
                    return HttpResponse(1)
            else:
                vote.rating_type=new_vote
                vote.save()
                if(new_vote):
                    return HttpResponse(1)
                else:
                    return HttpResponse(-1)

    return HttpResponse('not logged in')


# Function for adding all of the songs of a specified album to our db.
# album_json is a specific dictionary found in search methods.
# album_model_obj is the object reference of the album
#       (This is required to set the one to many field in Song)
def add_albums_songs(album_json, album_model_obj):
    album_tracks = sp.album_tracks(album_json["id"])
    #print(json.dumps(album_tracks, indent=4))
    album_tracks = album_tracks["items"]

    for json_obj in album_tracks:
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

        #artist stuff
        album_artists_list = [] # list of track's artists formatted how we want
        for artist_obj in track_artists:
            artist_name = artist_obj["name"]
            album_artists_list.append(artist_name)

        track_info = {
            "id" : track_id,
            "name" : track_name,
            "number" : track_number,
            "disc" : json_obj["disc_number"],
            "explicit" : track_explicit,
            "artists" : track_artists_list,
            "album_artists" : album_artists_list,
            "release_date" : album_json["release_date"]
        }

        object, created = Song.objects.get_or_create(
            id=track_info["id"],
            defaults = {
            "name" : track_info["name"],
            "artist" : track_info["artists"][0],
            "release_date" : track_info["release_date"],
            "track_number" : json_obj["track_number"],
            "disc" : track_info["disc"],
            "album_id" : album_model_obj,
            "duration_ms" : json_obj["duration_ms"],
            "explicit" : json_obj["explicit"]
            }
        )
        if created:
            print(f""+str(object)+" : "+track_info["name"]+" has been added." )

@require_GET
def search_album(request):
    form = SongForm()
    return render(request, "search_album.html", {"form": form, "albums": None})

@require_POST
def search_album_results(request):
    form = SongForm(request.POST)

    if form.is_valid():
        album_query = form.cleaned_data["song_name"]
        albums_json = sp.search(album_query, type="album", limit=10) # json with song information

        albums_json = albums_json["albums"]
        all_albums = []
        for json_obj in albums_json["items"]:
            album_id = json_obj["id"]
            album_name = json_obj["name"]
            album_release_date = json_obj["release_date"]
            album_type = json_obj["album_type"]
            album_total_tracks = json_obj["total_tracks"]
            album_artists = json_obj["artists"]
            album_cover_art = json_obj["images"][1]["url"]
            # cover is hardcoded rn but seems consistent from spotify
            album_artists_list = []
            for artist_obj in album_artists:
                artist_name = artist_obj["name"]
                album_artists_list.append(artist_name)

            album_info = {
                "id" : album_id,
                "name" : album_name,
                "release_date" : album_release_date,
                "type" : album_type,
                "total_tracks" : album_total_tracks,
                "artists" : album_artists_list,
                "cover" : album_cover_art
            }

            all_albums.append(album_info)
            #print(json.dumps(album_info, indent=4, sort_keys=True))
        if len(all_albums) == 0:
            return render(request, "search_album.html", {"form": form, "albums_empty": True})
        return render(request, "search_album.html", {"form": form, "albums": all_albums})
    else:
        print("Invalid form in search_album_results")
    return render(request, "search_album.html", {"form": form, "albums": None})


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
        songs_json = sp.search(track_query, limit=10) # json with song information

        final_songs_list = []

        songs_json = songs_json["tracks"]
        for json_obj in songs_json["items"]:
            album_json = json_obj["album"] # album json object
            album_id = album_json["id"] # track's album id
            album_artists_list = []

            for artist_obj in album_json["artists"]:
                artist_name = artist_obj["name"]
                album_artists_list.append(artist_name)

            track_info = {
                "id" : json_obj["id"],
                "name" : json_obj["name"],
                "number" : json_obj["track_number"],
                "explicit" : json_obj["explicit"],
                "artists" : json_obj["artists"][0]["name"], #TEMPORARY
                "album_id" : album_id,
                "album_name" : album_json["name"],
                "album_release_date" : album_json["release_date"],
                "album_artists" : album_artists_list,
            }
            #print(f"Track info: {json.dumps(track_info, indent=4)}")
            final_songs_list.append(track_info)

        return render(request, "search_song.html",
        {"form_info": form, "songs": final_songs_list})
    else:
        print("unsuccessful :(")

    return render(request, "search_song.html", {"form_info": form, "songs": None})

# Playlist Page functions
@require_GET
def playlist_song(request, list_id):
    form = SongForm()
    playlist = Playlist.objects.get(pk=list_id)
    return render(request, "addsongs_playlist.html", {"form": form, 'playlist': playlist})

@require_POST
def playlist_song_results(request, list_id):
    form = SongForm(request.POST)

    if form.is_valid():
        # find song list from spotipy and return the list in the form of a parameter in our render
        track_query = "track:"+form.cleaned_data["song_name"]
        songs_json = sp.search(track_query, limit=10) # json with song information

        final_songs_list = []

        songs_json = songs_json["tracks"]
        for json_obj in songs_json["items"]:
            album_json = json_obj["album"] # album json object
            album_id = album_json["id"] # track's album id
            album_artists_list = []

            for artist_obj in album_json["artists"]:
                artist_name = artist_obj["name"]
                album_artists_list.append(artist_name)

            track_info = {
                "id" : json_obj["id"],
                "name" : json_obj["name"],
                "number" : json_obj["track_number"],
                "explicit" : json_obj["explicit"],
                "artists" : json_obj["artists"][0]["name"], #TEMPORARY
                "album_id" : album_id,
                "album_name" : album_json["name"],
                "album_release_date" : album_json["release_date"],
                "album_artists" : album_artists_list,
            }
            #print(f"Track info: {json.dumps(track_info, indent=4)}")
            final_songs_list.append(track_info)

        playlist = Playlist.objects.get(pk=list_id)
        return render(request, "addsongs_playlist.html", {"form_info": form,
        "songs": final_songs_list, 'playlist': playlist})
    else:
        print("unsuccessful :(")

    return render(request, "addsongs_playlist.html",
    {"form_info": form, "songs": final_songs_list, 'playlist': playlist})


def add_song(request, list_id, song_id):
    # First, all of the shit related to adding the song to our db if
    # it doesn't exist yet.
    track = sp.track(f"spotify:track:"+song_id)

    album_artists_list = []
    for artist_obj in track["artists"]:
        artist_name = artist_obj["name"]
        album_artists_list.append(artist_name)

    album_info = {
        "id" : track["album"]["id"],
        "name" : track["album"]["name"],
        "release_date" : track["album"]["release_date"],
        "type" : track["album"]["type"],
        "total_tracks" : track["album"]["total_tracks"],
        "artists" : album_artists_list,
        "cover" : track["album"]["images"][1]["url"]
    }

    object, created = Album.objects.get_or_create(
        id=album_info["id"],
        name=album_info["name"],
        artist=album_info["artists"][0], #TEMPORARY
        release_date=album_info["release_date"],
        total_tracks=album_info["total_tracks"],
        cover=album_info["cover"]
        )
    if created:
        add_albums_songs(album_info, object)

    # Now add the song to the playlist specified by list_id.
    playlist = Playlist.objects.get(pk=list_id)
    song = Song.objects.get(pk=song_id)
    playlist.songs.add(song)
    playlist.save()
    songs = playlist.songs.all()
    all_songs = list(songs)
    n = 1
    list_songs = [all_songs[i:i+n] for i in range(0, len(all_songs), n)]
    listsong = list(list_songs)
    return render(request, 'addsongs.html', {'playlist': playlist, 'listsong': listsong})

# Playlist Page functions
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

def addsongs_view(request, list_id):
    playlist = Playlist.objects.get(pk=list_id)
    return render(request, "addsongs.html", {'playlist': playlist})

#Displays Album - and hopefully the tracks of the album uhh
def album_info(request, id):
    # id = '2r6OAV3WsYtXuXjvJ1lIDi' test value

    # Get the json for this album id
    album = sp.album(f"spotify:album:"+id)

    album_artists_list = []
    for artist_obj in album["artists"]:
        artist_name = artist_obj["name"]
        album_artists_list.append(artist_name)

    album_info = {
        "id" : album["id"],
        "name" : album["name"],
        "release_date" : album["release_date"],
        "type" : album["type"],
        "total_tracks" : album["total_tracks"],
        "artists" : album_artists_list,
        "cover" : album["images"][1]["url"] #TEMPORARY
    }

    # Now check if this album already exists.
    object, created = Album.objects.get_or_create(
        id=album_info["id"],
        defaults = {
        "name" : album_info["name"],
        "artist" : album_info["artists"][0], #TEMPORARY
        "release_date" : album_info["release_date"],
        "total_tracks" : album_info["total_tracks"],
        "cover" : album_info["cover"]
        }
        )
    if created:
        add_albums_songs(album_info, object)

    album_tracks = []
    all_our_songs = Song.objects.filter(album_id=object)

    for song in all_our_songs:
        # This inserts each song in order according to
        # its track number and the disc its on.
        album_tracks.insert(song.track_number * song.disc, song.name)

    return render(request, "album_info.html", {"id": id, "songs": all_our_songs})

# This method does two things:
# 1. Check if song's album exists in our db. If it
# doesn't then add the album and all of its songs.
# 2. Return render of songinfo.html with the song id.
def songinfo(request, music_id):
    # Get the json object for this specific track.
    track = sp.track(f"spotify:track:"+music_id)

    album_artists_list = []
    for artist_obj in track["artists"]:
        artist_name = artist_obj["name"]
        album_artists_list.append(artist_name)

    # Get the album info of this song's album.
    album_info = {
        "id" : track["album"]["id"],
        "name" : track["album"]["name"],
        "release_date" : track["album"]["release_date"],
        "type" : track["album"]["type"],
        "total_tracks" : track["album"]["total_tracks"],
        "artists" : album_artists_list,
        "cover" : track["album"]["images"][1]["url"]
    }

    # Now check if this album already exists.
    object, created = Album.objects.get_or_create(
        id=album_info["id"],
        defaults = {
        "name" : album_info["name"],
        "artist" : album_info["artists"][0], #TEMPORARY
        "release_date" : album_info["release_date"],
        "total_tracks" : album_info["total_tracks"],
        "cover" : album_info["cover"]
        }
        )
    if created: # if it was new, add all of its songs to our db
        add_albums_songs(album_info, object)

    songid = Song.objects.get(pk=music_id)
    return render(request, 'songinfo.html', {'songid': songid,
    "album": {
        "name": album_info["name"],
        "id": album_info["id"]}})

def settings_general(request):
    return render(request, 'settings_general.html')

def settings_security(request):
    return render(request, 'settings_security.html')

def settings_reset_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(reverse('settings_account'))
        else:
            messages.success(request, ('One or More Requirements Not Fulfiled!'))
            return redirect(reverse('settings_reset_password'))
    else:
        form = PasswordChangeForm(user=request.user)

        args = {'form': form}
        return render(request, 'settings_reset_password.html', args)

def settings_account(request):
      if request.method == 'POST':
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid:
          form.save()
          messages.success(request, ('Settings has been Saved!'))
          return render(request, 'settings_account.html')
      else:
        form = EditUserForm(instance=request.user)
        args = {
          'form': form,
          }
        return render(request, 'settings_account.html', args)

def profile(request):
    return render(request, 'profile.html', {})

def search_user(request):
    if request.method == "POST":
        searched = request.POST['searched']
        user_names = User.objects.filter(username__contains=searched)
        friends = Friend.objects.friends(request.user)
        return render(request, 'events/search_user.html', {'searched': searched, 'user_names': user_names,
                                                               'friends': friends})

def my_view(request):
    # List of this user's friends
    all_friends = Friend.objects.friends(request.user)

    # List all unread friendship requests
    requests = Friend.objects.unread_requests(user=request.user)

    # List all rejected friendship requests
    rejects = Friend.objects.rejected_requests(user=request.user)

    # List of this user's followers
    all_followers = Following.objects.followers(request.user)

    # List of who this user is following
    following = Following.objects.following(request.user)

    ### Managing friendship relationships
    other_user = User.objects.get(pk=1)
    new_relationship = Friend.objects.add_friend(request.user, other_user)
    Friend.objects.are_friends(request.user, other_user) == True
    Friend.objects.remove_friend(other_user, request.user)

    # Can optionally save a message when creating friend requests
    some_other_user = User.objects.get(pk=2)
    message_relationship = Friend.objects.add_friend(
        from_user=request.user,
        to_user=some_other_user,
        message='Hi, I would like to be your friend',
    )

    # Attempting to create an already existing friendship will raise
    # `friendship.exceptions.AlreadyExistsError`, a subclass of
    # `django.db.IntegrityError`.
    dupe_relationship = Friend.objects.add_friend(request.user, other_user)
    AlreadyExistsError: u'Friendship already requested'

    # Create request.user follows other_user relationship
    following_created = Following.objects.add_follower(request.user, other_user)

    # Attempting to add an already existing follower will also raise
    # `friendship.exceptions.AlreadyExistsError`,
    dupe_following = Following.objects.add_follower(request.user, other_user)
    AlreadyExistsError: u"User 'alice' already follows 'bob'"

    was_following = Following.objects.remove_follower(request.user, other_user)

    # Create request.user blocks other_user relationship
    block_created = Block.objects.add_block(request.user, other_user)

    # Remove request.user blocks other_user relationship
    block_remove = Block.objects.remove_block(request.user, other_user)

# Register Page and Login/Logout relevant functions.
def registerPage(request):
    form = CreateUserForm()

    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, 'Account was created for ' + user)

            return redirect('login')


    context = {'form': form}
    return render(request, 'register.html', context)

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, "Username OR Password is incorrect")

    context = {}
    return render(request, 'login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

def topChart(request):
    #form = SearchForm() No search form exists, so commenting out.
    return render(request, 'topcharts.html')


def topChart(request):
    return render(request, 'topcharts.html')

def topChart_Global(request):
    return render(request, 'GlobalTopChart.html')

def topChart_Canada(request):
    return render(request, 'CanadaTopChart.html')

def topChart_Japan(request):
    return render(request, 'JapanTopChart.html')

def topChart_Mexico(request):
    return render(request, 'MexicoTopChart.html')

def topChart_USA(request):
    return render(request, 'USATopChart.html')
