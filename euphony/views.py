from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse
from django.db.utils import OperationalError
from django.core.exceptions import ObjectDoesNotExist # for checking if row exists
from euphony.models import Playlist
from .forms import PlaylistForm
    #ProfileForm

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

from .models import Song, UserToken

from django.contrib import messages
from .forms import EditUserForm

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
        
        print(json.dumps(albums_json, indent=4, sort_keys=True))
        # Fields we want:
        # artists (get "name" from each item in artists list)
        # album_type
        # id
        # name
        # release date
        # total_tracks
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

            object, created = Album.objects.get_or_create(
            id=album_info["id"],
            name=album_info["name"],
            artist=album_info["artists"][0],
            release_date=album_info["release_date"],
            total_tracks=album_info["total_tracks"],
            cover=album_info["cover"]
            )

            all_albums.append(album_info)
            print(json.dumps(album_info, indent=4, sort_keys=True))
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
        songs_json = sp.search(track_query) # json with song information
        #songs = json.load(songs_json)
        #tracks = songs_json["tracks"]
        #print(json.dumps(songs_json, indent=4, sort_keys=True))

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

def addsongs_view(request):
    return render(request, "addsongs.html", {})

#Displays Album - and hopefully the tracks of the album uhh
def album_info (request, id):
    id = '2r6OAV3WsYtXuXjvJ1lIDi'
    return render(request, "album_info.html", {"id": id})

def songinfo(request, music_id):
    songid = Song.objects.get(pk=music_id)
    return render(request, 'songinfo.html', {'songid': songid})

def settings_general(request):
    return render(request, 'settings_general.html')

def settings_security(request):
    return render(request, 'settings_security.html')

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

def topChart_post(request):
    context  = {}
    return render(request, 'topcharts.html', context)

def search_users(request):
    if request.method == "POST":
        searched2 = request.POST['searched2']
        users = User.objects.filter(username__contains=searched2)
        friends = Friend.objects.friends(request.user)
        print(request.user, searched2)
        other_user = User.objects.get(pk=1)
        return render(request, 'events/search_users.html', {'searched2': searched2, 'users':users, 'friends':friends, 'other_user':other_user})
    else:
        return render(request, 'events/search_users.html', {})


def list_users(request):
    user_list = User.objects.all()
    return render(request, 'events/users.html', {'user_list': user_list})

def show_user(request, user_id):
    user = User.objects.get(pk=user_id)
    allfriends = Friend.objects.friends(user)
    #print(request.user, user)
    return render(request, 'events/show_user.html', {'user': user, 'allfriends':allfriends})


