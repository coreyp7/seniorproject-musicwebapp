from tkinter import X
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse
from django.db.utils import OperationalError
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist # for checking if row exists
from euphony.models import Playlist, Album, User_Profile, User_Setting_Ext
from .forms import PlaylistForm
from .region_codes import region_codes
    #ProfileForm
from friendship.models import FriendshipRequest
from django.contrib import messages
from friendship.models import Friend, Follow, Block
from django.contrib.auth import authenticate, login, logout
#import datetime
from django_comments_xtd.models import XtdComment
from django.contrib.contenttypes.models import ContentType
import itertools
from datetime import datetime, timedelta


import django_comments
from django_comments import signals
from django_comments.views.utils import next_redirect, confirmation_view
from django.contrib.sites.shortcuts import get_current_site
from django_comments.views.moderation import delete, perform_delete

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from numpy.random import default_rng, shuffle
import json
import numpy as np
import pytz
utc=pytz.UTC

from .cashe_handler import DatabaseTokenHandler
from .spotify_queries import *

from .forms import SongForm, CreateUserForm
from .models import *

from .models import Song, UserToken, Song_rating

from django.contrib import messages
from .forms import EditUserForm

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

scope = "user-library-read user-top-read"
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

def prepare_post_dicts(song_list, user_friends):

    '''
    puts together a list of post dictioies, sorts them by weight, and list a friend that liked it. (not 100% tested)

    by the end of this proccess a post dict should be {song id, number of ratings, post weight, name of a friend or None if no friends}
    '''

    posts = [{ "song_id" : item[0]["id"], "cover" :  item[0]["cover"] , "ratings" : item[1]} for item in zip(song_list, get_song_rating_numbers(song_list))]

    #assign weights to posts based on friends upvotes

    for post in posts:
        print(post['cover'])
        #give posts with friends likes a higher ranking
        friend_ratings = list( Song_rating.objects.filter(user_id__in = user_friends, song_id=post["song_id"]) )
        post['weight'] = post['ratings'] + 2*len(friend_ratings)

    shuffle(posts)
    posts = posts[:50]
    posts.sort(key = lambda item : item['weight'], reverse=True )


    return posts

def dash(request):

    '''
    returns a webapge of recommendations, or if an account is unlinked it returns "account not linked with spotify"

    idea : so I don't need to think about ranking friends, and comments. display resent comments, and resent playlists display an extra two feeds of friend comments.
    '''

    id_list = []
    posts = []
    '''
    #check if user is logged in
    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):

        #get spotify client with user specific permissions
        temp_client = gen_client(user, scope)
        if temp_client != None:
            user_friends = Friend.objects.friends(user)
            #with friends list get a set of recommended ALBUMBS
            album_list = gen_recomendations(temp_client, user_friends, scope)
            #get the SONGS from those recommended albums from spotify
            song_list = get_song_list(temp_client, album_list)
            #prepare, and rank a list of post dicts
            posts = prepare_post_dicts(song_list, user_friends)
        # if user is logged in but not connected to spotify
        else:
            # Here we'll create a list of recommended songs from the user's upvotes.
            # If no upvotes are available, then recommend based off their initial picked genres.
            # (Get similar stuff ala spotify)
            pass

    else: # if it's an anonymous user, just get 50 random songs from our database.
        #when not logged in get 50 songs from the database and rank them
        songs = Song.objects.all()
        indexs = rng.choice(range(len(songs)), size=50, replace=False)
        song_list = np.array(list(songs))[indexs]
        posts = [{ "song" : item[0] , "ratings" : item[1], "friend_name" : None} for item in zip(song_list, get_song_rating_numbers(song_list)) ]
        posts.sort(key = lambda item : item['ratings'], reverse=True )
    '''
    friends_ratings = []
    friends_comments = []
    friends_new_playlists = []

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):
        temp_client = gen_client(user, scope)
        # here we will get friends ratings, comments, and new playlists.
        # get the list of rows of all this users' friends.
        user_friends = Friend.objects.friends(user)

        if temp_client != None:
            # signed in and connected to spotify
            # get recommendations from spotify for their connected account.
            #with friends list get a set of recommended ALBUMBS
            album_list = gen_recomendations(temp_client, user_friends, scope)
            #get the SONGS from those recommended albums from spotify
            song_list = get_song_list(temp_client, album_list)
            #prepare, and rank a list of post dicts
            posts = prepare_post_dicts(song_list, user_friends)
            #NOTE: ADD 'posts' to 'all_dashbaord_feed' following the format of the other dictionaries.
            # Example dict:
            # {
            #       'post_type' : "recommendation",
            #       'friend_id" : id of user,
            #       'item_type' : type of content (song, album, or playlist),
            #       'item_id' : id of the content (song, album, or playlist),
            #       'song_album_cover' : cover link of the song/album, null if a playlist.
            #       'rating_type' : True or False, indicating type of rating
            # }
        else: # signed in, not connected to spotify
            # as it turns out the recommendation end point doesn't user permissions
            # so gen_recomendation has been modifed to accept spotipy clients with out permissions\
            # - nico
            album_list = gen_recomendations(sp, user_friends, scope)
            song_list = get_song_list(sp, album_list)
            posts = prepare_post_dicts(song_list, user_friends)

        # first, ratings:
        friends_ratings = get_users_friend_rating_activity(user_friends)
        # second, comments:
        friends_comments =  get_users_friend_comment_activity(user_friends)
        # third,
        friends_new_playlists = get_users_friend_playlist_activity(user_friends)

    else: # anonymous user
        try:
            songs = Song.objects.all()
            indexs = rng.choice(range(len(songs)), size=50, replace=False)
            song_list = np.array(list(songs))[indexs]
            posts = [{ "song" : item[0] , "ratings" : item[1], "friend_name" : None} for item in zip(song_list, get_song_rating_numbers(song_list)) ]
            posts.sort(key = lambda item : item['ratings'], reverse=True )
        except:
            return HttpResponse(":( please sir/madam may I have some songs (for anonymous browings the database needs 50 songs. run the dash with a linked account one or twice for anon browsing to work right) ")

    all_dashboard_feed = list(itertools.chain(
        friends_ratings,
        friends_comments,
        friends_new_playlists)) # NICO put recommendations in here
        # just assign each song a random date in the past week or something so that it
        # randomizes the recommendations: this is up to you how you wanna implement.

    all_dashboard_feed.sort(key=lambda x: x["date"])
    print(all_dashboard_feed)
    return render(request, 'dash.html', {'recommendations' : posts,
    'ratings': friends_ratings, 'comments': friends_comments, 'playlists': friends_new_playlists,
    'feed': all_dashboard_feed})
    # plan: return dictionary called 'recommendations' which contains objects which specify:
    # 1. type and 2. information for that type of object
    # The different types are:
    # 1. 'recommendation' (what's there now) : leave out of the picture for now.
    # 2. DONE
    # 3. DONE
    # 4. DONE
    # 5. 'generic' (just a text post) : we could use the comments extension for this, no idea. Ignore for now.
    #
    # Example dict for recommendation:
    # {
    #       'post_type' : "recommendation",
    #       'friend_id" : id of friend related to this "post",
    #       'item_type' : type of content (song is the only thing that's recommended rn),
    #       'item_id' : id of the content (song),
    #       'song_album_cover' : cover link of the song/album, null if a playlist.
    # }
    # So process: filter out the results out of our tables,
    # put it all into dictionaries formatted like this and
    # put it in a list organized by date (front end shouldnt have to do this at all)

    # NOW 4/21/22 12:55PM: Next, convert nicos shit into these dictionaries.
    # Then created an organized list based on date.

def get_users_friend_playlist_activity(user_friends):
    today = datetime.now().utcnow().date() # today's date
    week_ago = today - timedelta(7) # a week in the past
    playlists_dict = []

    for friend in user_friends:
        friend_playlists = Playlist.objects.filter(user_id=friend, date_created__range=[week_ago,today])
        for playlist in friend_playlists:
            new_dict = {
                'post_type' : 'friend_playlist',
                'friend_id' : friend.id,
                'playlist_id' : playlist.id,
                'date' : playlist.date_created,
                'item_name' : playlist.name,
                'friend_name': friend.username
            }
            playlists_dict.append(new_dict)

    return playlists_dict

def get_users_friend_comment_activity(user_friends):
    today = datetime.now().utcnow().date() # today's date
    week_ago = today - timedelta(7) # a week in the past
    comments_dict = []

    for friend in user_friends:
        friend_comments = XtdComment.objects.filter(user=friend)
        print(friend_comments)
        for comment in friend_comments:
            print(comment._meta.get_fields())
            print(str(comment.content_type))
            if str(comment.content_type) == "euphony | song":
                cover = Song.objects.get(id=comment.object_pk).album_id.cover
                min = datetime.min.time()
                formatted_date = datetime.combine(comment.submit_date,min)
                song_ref = Song.objects.get(id=comment.object_pk)
                new_dict = {
                    'post_type' : 'friend_comment',
                    'friend_id' : friend.id,
                    'item_type' : "song",
                    'item_id' : comment.object_pk,
                    'song_album_cover' : cover,
                    'comment_message' : comment.comment,
                    'date' : comment.submit_date.date(),
                    'item_name' : song_ref.name,
                    'friend_name': friend.username
                }
                comments_dict.append(new_dict)
            elif str(comment.content_type) == "euphony | album":
                cover = Album.objects.get(id=comment.object_pk).cover
                min = datetime.min.time()
                album_ref = Album.objects.get(id=comment.object_pk)
                new_dict = {
                    'post_type' : 'friend_comment',
                    'friend_id' : friend.id,
                    'item_type' : "album",
                    'item_id' : comment.object_pk,
                    'song_album_cover' : cover,
                    'comment_message' : comment.comment,
                    'date' : comment.submit_date.date(),
                    'item_name' : album_ref.name,
                    'friend_name': friend.username
                }
                comments_dict.append(new_dict)
            else: # playlist
                min = datetime.min.time()
                playlist_ref = Playlist.objects.get(id=comment.object_pk)
                new_dict = {
                    'post_type' : 'friend_comment',
                    'friend_id' : friend.id,
                    'item_type' : "playlist",
                    'item_id' : comment.object_pk,
                    'comment_message' : comment.comment,
                    'date' : comment.submit_date.date(),
                    'item_name' : playlist_ref.name,
                    'friend_name': friend.username
                }
                comments_dict.append(new_dict)

    return comments_dict

def get_users_friend_rating_activity(user_friends):
    today = datetime.now().utcnow().date() # today's date
    week_ago = today - timedelta(7) # a week in the past
    ratings_dict = [] # Our ratings list, containing formatted dicts.
    for friend in user_friends:
            friend_song_ratings = Song_rating.objects.filter(
                user_id=friend,
                date__range=[week_ago, today])
            friend_album_ratings = Album_rating.objects.filter(
                user_id=friend,
                date__range=[week_ago, today])
            friend_playlist_ratings = Playlist_rating.objects.filter(
                user_id=friend,
                date__range=[week_ago, today])

            for rating in friend_song_ratings:

                new_dict = {
                    'post_type' : "friend_rating",
                    'friend_id' : friend.id,
                    'item_type' : "song",
                    'item_id' : rating.song_id.id,
                    'song_album_cover' : rating.song_id.album_id.cover,
                    'rating_type' : rating.rating_type,
                    'date' : rating.date.date(),
                    'friend_name' : friend.username,
                    'item_name' : rating.song_id.name
                }
                ratings_dict.append(new_dict)

            for rating in friend_album_ratings:
                new_dict = {
                    'post_type' : "friend_rating",
                    'friend_id' : friend.id,
                    'item_type' : "album",
                    'item_id' : rating.album_id.id,
                    'song_album_cover' : rating.album_id.cover,
                    'rating_type' : rating.rating_type,
                    'date' : rating.date.date(),
                    'friend_name' : friend.username,
                    'item_name' : rating.album_id.name
                }
                ratings_dict.append(new_dict)

            for rating in friend_playlist_ratings:
                new_dict = {
                    'post_type' : "friend_rating",
                    'friend_id' : friend.id,
                    'item_type' : "playlist",
                    'item_id' : rating.playlist_id.id,
                    'rating_type' : rating.rating_type,
                    'date' : rating.date.date(),
                    'friend_name' : friend.username,
                    'item_name' : rating.playlist_id.name
                }
                ratings_dict.append(new_dict)
    return ratings_dict


def proccess_vote(request):

    '''
    works with the js vote function I wrote to take in a song id
    to create a rating object associated with that user, and song.
    this then sends back a 1, or -1 to update the frontend vote count.

    if a user preses a button two times in a row then that vote is deleted
    '''

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id))):
        song = Song.objects.get(id=request.POST['song'])
        rating = list(Song_rating.objects.filter(user_id=user, song_id=song))
        new_vote = (int(request.POST['vote']) == 1)
        if len(rating) == 0:
            #if no votes for that user song pair make a new post object
            vote = Song_rating.objects.create(song_id=song, user_id=user, rating_type=new_vote, date=datetime.now().utcnow().date())
            if(new_vote):
                return HttpResponse(1)
            else:
                return HttpResponse(-1)
        else:
            vote = rating[0]
            old_vote = vote.rating_type
            #if old vote == new vote just delete that vote, otherwise modify the vote
            if(old_vote == new_vote):
                vote.delete()
                if(old_vote):
                    return HttpResponse(-1)
                else:
                    return HttpResponse(1)
            else:
                vote.delete()
                Song_rating.objects.create(song_id=song, user_id=user, rating_type=new_vote, date=datetime.now().utcnow().date())
                if(new_vote):
                    return HttpResponse(2)
                else:
                    return HttpResponse(-2)

    return HttpResponse('not logged in')


@require_GET
def search(request):
    form = SongForm()
    return render(request, "search.html", {"form": form})

# Function for search page when form has been submitted.
# 1. Query for songs on spotify and create a list of dictionaries with information we need to display.
# 2. Query for albums on spotify and create a list of dictionaries with information we need to display.
# Also put a boolean named 'results' in our render dictionary to tell the front end the form was submitted.
def search_results(request):
    #form = SongForm(request.POST)
    if request.method == "POST":
        search_query = request.POST['search_query']
        # 1. Get Song query results and put it in 'final_songs_list'

        # find song list from spotipy and return the list in the form of a parameter in our render
        track_query = "track:"+search_query
        songs_json = sp.search(track_query, limit=10) # json with song information

        final_songs_list = []

        songs_json = songs_json["tracks"]
        for json_obj in songs_json["items"]:
            album_json = json_obj["album"] # album json object
            album_id = album_json["id"] # track's album id

            album_artists = []
            for artist_obj in json_obj["artists"]:
                album_artists.append(artist_obj['name'])
            album_artists_str = ", ".join(album_artists)

            track_info = {
                "id" : json_obj["id"],
                "name" : json_obj["name"],
                "number" : json_obj["track_number"],
                "explicit" : json_obj["explicit"],
                "artists" : album_artists_str,
                "album_id" : album_id,
                "album_name" : album_json["name"],
                "album_release_date" : album_json["release_date"],
                "album_cover" : album_json["images"][1]["url"]
                # IN "album_cover", change to 0 for bigger pic, 2 for smaller pic
            }

            # If it is in a compilation, we just flat out ignore it and don't show it.
            if album_json["album_type"] != 'compilation':
                final_songs_list.append(track_info)

        # 2. Get Album query results and put it in 'all_albums'
        album_query = search_query
        albums_json = sp.search(album_query, type="album", limit=10) # json with album information

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
                album_artists_list.append(artist_obj['name'])
            album_artists_str = ", ".join(album_artists_list)

            album_info = {
                "id" : album_id,
                "name" : album_name,
                "release_date" : album_release_date,
                "type" : album_type,
                "total_tracks" : album_total_tracks,
                "artists" : album_artists_str,
                "cover" : album_cover_art
            }

            # If it is a compilation, we just flat out ignore it and don't show it.
            if album_info["type"] != 'compilation':
                all_albums.append(album_info)

        # 3: search user query.
        users = User.objects.filter(username__contains=search_query)
        try:
            self = User.objects.get(pk=request.user.id)
            users = filter(lambda user: Block.objects.is_blocked(self, user) != True, users)
        except:
            pass
        friends = Friend.objects.friends(User.objects.get(pk=1))

        # 4: Lastly, playlist search query. (across all playlist)
        playlists = Playlist.objects.filter(name__contains=search_query)
        """playlists_dict = []
        for playlist in playlists:
            playlist_obj = {
                "id" : playlist.id,
                "name" : playlist.name
                /"user_id" : playlist.user_id.id
            }
            playlists_dict.append(playlist_obj)
        """
        return render(request, "search.html",
        {"songs": final_songs_list, "albums": all_albums, "results": True,
        "users": users, "friends": friends, "playlists": playlists})
    else:
        print("unsuccessful :(")

    return render(request, "search.html", {"songs": None})

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

            album_artists = []
            for artist_obj in album_json["artists"]:
                album_artists.append(artist_obj['name'])
            album_artists_str = ", ".join(album_artists)

            track_info = {
                "id" : json_obj["id"],
                "name" : json_obj["name"],
                "number" : json_obj["track_number"],
                "explicit" : json_obj["explicit"],
                "artists" : json_obj["artists"][0]["name"], #TEMPORARY
                "album_id" : album_id,
                "album_name" : album_json["name"],
                "album_release_date" : album_artists_str,
                "album_artists" : album_artists_str,
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

    album_artists = []
    for artist_obj in track["album"]["artists"]:
        album_artists.append(artist_obj['name'])
    album_artists_str = ", ".join(album_artists)

    album_info = {
        "id" : track["album"]["id"],
        "name" : track["album"]["name"],
        "release_date" : track["album"]["release_date"],
        "type" : track["album"]["type"],
        "total_tracks" : track["album"]["total_tracks"],
        "artists" : album_artists_str,
        "cover" : track["album"]["images"][1]["url"]
    }

    object, created = Album.objects.get_or_create(
        id=album_info["id"],
        name=album_info["name"],
        artists=album_info["artists"],
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

    return redirect('addsongs_view', list_id=playlist.id )


# Playlist Page functions
def allplaylists_view(request):
    if request.user.is_authenticated:
        playlists = Playlist.objects.filter(user_id=request.user)
        return render(request,'playlists.html',{'playlists': playlists})
    else:
        return redirect('login')

def create_playlist(request):
    submitted = False
    if request.method == "POST":
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False) # tells django "don't put into db"
            playlist.user_id = request.user
            playlist.date_created = datetime.now().utcnow().date()
            playlist.save()

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

def delete_song(request, list_id, song_id):
    playlist = Playlist.objects.get(pk=list_id)
    song = playlist.songs.remove(song_id)
    messages.success(request, ('Song Has Been Deleted!'))
    return redirect('addsongs_view', list_id=playlist.id)

def addsongs_view(request, list_id):
    playlist = Playlist.objects.get(pk=list_id)

    users_playlist = False
    if playlist.user_id == request.user:
        users_playlist = True
    songs = playlist.songs.all()

    upvotes = 0
    downvotes = 0
    try:
        list_ratings = Playlist_rating.objects.filter(playlist_id=list_id)
        for rating in list_ratings:
            if rating.rating_type:
                upvotes += 1
            elif not rating.rating_type:
                downvotes += 1
    except:
        print("Except gone through")

    user_upvoted = False
    user_downvoted = False

    already_saved = False

    if request.user.is_authenticated:
        try:
            users_rating = Song_rating.objects.get(list_id=list_id.id, user_id=request.user)
            if users_rating.rating_type == True:
                user_upvoted = True
            elif users_rating.rating_type == False:
                user_downvoted = True
        except:
            pass

        # Does user already have this saved?
        try:
            is_this_playlist_saved = User_Profile.objects.get(user=request.user, saved_playlist=list_id)
            already_saved = True
        except:
            pass

    return render(request, "addsongs.html", {'playlist': playlist, 'songs': songs,
    "upvotes": upvotes, "downvotes": downvotes,
    "user_upvoted": user_upvoted, "user_downvoted": user_downvoted,
    "already_saved": already_saved,
    "users_playlist":users_playlist})

def save_playlist(request, list_id):
    user = request.user
    playlist = Playlist.objects.get(pk=list_id)
    saved_playlist = User_Profile.objects.create(user=user, saved_playlist=playlist)
    saved_playlist.save()
    return redirect('addsongs_view', playlist.id)

def unsave_playlist(request, list_id):
    user = request.user
    playlist = Playlist.objects.get(pk=list_id)
    saved_playlist = User_Profile.objects.get(user=user, saved_playlist=playlist)
    saved_playlist.delete()
    return redirect('addsongs_view', playlist.id)

#Displays Album - and hopefully the tracks of the album uhh
def album_info(request, id):
    # id = '2r6OAV3WsYtXuXjvJ1lIDi' test value

    # Get the json for this album id
    album = sp.album(f"spotify:album:"+id)

    album_artists = []
    for artist_obj in album["artists"]:
        album_artists.append(artist_obj['name'])
    album_artists_str = ", ".join(album_artists)

    album_info = {
        "id" : album["id"],
        "name" : album["name"],
        "release_date" : album["release_date"],
        "type" : album["type"],
        "total_tracks" : album["total_tracks"],
        "artists" : album_artists_str,
        "cover" : album["images"][1]["url"] #TEMPORARY
    }

    # Now check if this album already exists.
    object, created = Album.objects.get_or_create(
        id=album_info["id"],
        defaults = {
        "name" : album_info["name"],
        "artists" : album_info["artists"],
        "release_date" : album_info["release_date"],
        "total_tracks" : album_info["total_tracks"],
        "cover" : album_info["cover"]
        }
        )
    if created:
        add_albums_songs(album_info, object)

    album_tracks = []
    all_our_songs = Song.objects.filter(album_id=object)

    song_counter = 1
    for song in all_our_songs:
        # Create dictionaries for the album_info.html to easily display, handle the logic here.

        new_song = {
            "id" : song.id,
            "album_id" : song.album_id,
            "name" : song.name,
            "artists" : song.artists,
            "duration" : convertMillis(song.duration_ms),
            "explicit" : song.explicit,
            "release_date" : song.release_date,
            "track_number" : song.track_number,
            "disc" : song.disc,
            "allow_comments" : song.allow_comments
        }
        album_tracks.append(new_song)

    albumid = Album.objects.get(pk=id)

    upvotes = 0
    downvotes = 0
    try:
        album_ratings = Album_rating.objects.filter(album_id=albumid.id)
        for rating in album_ratings:
            if rating.rating_type:
                upvotes += 1
            elif not rating.rating_type:
                downvotes += 1
    except:
        print("Except gone through")


    user_upvoted = False
    user_downvoted = False

    if request.user.is_authenticated:
        try:
            users_rating = Album_rating.objects.get(album_id=albumid.id, user_id=request.user)
            if users_rating.rating_type == True:
                user_upvoted = True
            elif users_rating.rating_type == False:
                user_downvoted = True
        except:
            pass

    return render(request, "album_info.html", {"albumid": albumid, "songs": album_tracks,
    "album": album_info,
    "upvotes": upvotes, "downvotes": downvotes,
    "user_voted": user_upvoted, "user_downvoted": user_downvoted})

def album_info_upvote(request, albumid):
    album_instance = Album.objects.get(pk=albumid)

    object, created = Album_rating.objects.get_or_create(
        user_id=request.user,
        album_id=album_instance)
    if created: # If new, assign time right now and save.
        object.date = datetime.now().utcnow().date()
        object.rating_type = True
        object.save()
    else: # If not new
        if not object.rating_type: # if its a downvote already, change it to be an upvote.
            object.rating_type = True
            object.date = datetime.now().utcnow().date()
            object.save()
        else: # User is pressing upvote button when it was already pressed, get rid of upvote.
            object.delete()
    return redirect('album_info', albumid, permanent=True)

def album_info_downvote(request, albumid):
    album_instance = Album.objects.get(pk=albumid)

    object, created = Album_rating.objects.get_or_create(
        user_id=request.user,
        album_id=album_instance)
    if created: # If new, assign time right now and save.
        object.date = datetime.now().utcnow().date()
        object.rating_type = False
        object.save()
    else: # If not new
        if object.rating_type: # if its a upvote already, change it to be an upvote.
            object.rating_type = False
            object.date = datetime.now().utcnow().date()
            object.save()
        else: # User is pressing upvote button when it was already pressed, get rid of upvote.
            object.delete()
    return redirect('album_info', albumid, permanent=True)

# This method does two things:
# 1. Check if song's album exists in our db. If it
# doesn't then add the album and all of its songs.
# 2. Return render of songinfo.html with the song id.
def songinfo(request, music_id):
    # Get the json object for this specific track.
    track = sp.track(f"spotify:track:"+music_id)

    track_artists = []
    for artist_obj in track["artists"]:
        track_artists.append(artist_obj['name'])
    track_artists_str = ", ".join(track_artists)

    # Get the album info of this song's album.
    album_info = {
        "id" : track["album"]["id"],
        "name" : track["album"]["name"],
        "release_date" : track["album"]["release_date"],
        "type" : track["album"]["type"],
        "total_tracks" : track["album"]["total_tracks"],
        "artists" : track_artists_str,
        "cover" : track["album"]["images"][1]["url"]
    }

    # Now check if this album already exists.
    object, created = Album.objects.get_or_create(
        id=album_info["id"],
        defaults = {
        "name" : album_info["name"],
        "artists" : album_info["artists"],
        "release_date" : album_info["release_date"],
        "total_tracks" : album_info["total_tracks"],
        "cover" : album_info["cover"]
        }
        )
    if created: # if it was new, add all of its songs to our db
        add_albums_songs(album_info, object)

    songid = Song.objects.get(pk=music_id)

    upvotes = 0
    downvotes = 0
    try:
        song_ratings = Song_rating.objects.filter(song_id=songid.id)
        for rating in song_ratings:
            if rating.rating_type:
                upvotes += 1
            elif not rating.rating_type:
                downvotes += 1
    except:
        print("Except gone through")

    user_upvoted = False
    user_downvoted = False

    if request.user.is_authenticated:
        try:
            users_rating = Song_rating.objects.get(song_id=songid.id, user_id=request.user)
            if users_rating.rating_type == True:
                user_upvoted = True
            elif users_rating.rating_type == False:
                user_downvoted = True
        except:
            pass


    return render(request, 'songinfo.html', {'songid': songid, "song_artists": track_artists_str,
    "album": {
        "name": album_info["name"],
        "id": album_info["id"]},
    "upvotes": upvotes, "downvotes": downvotes,
    "user_voted": user_upvoted, "user_downvoted": user_downvoted})

def songinfo_upvote(request, songid):
    song_instance = Song.objects.get(pk=songid)

    object, created = Song_rating.objects.get_or_create(
        user_id=request.user,
        song_id=song_instance)
    if created: # If new, assign time right now and save.
        object.date = datetime.now().utcnow().date()
        object.rating_type = True
        object.save()
    else: # If not new
        if not object.rating_type: # if its a downvote already, change it to be an upvote.
            object.rating_type = True
            object.date = datetime.now().utcnow().date()
            object.save()
        else: # User is pressing upvote button when it was already pressed, get rid of upvote.
            object.delete()
    return redirect('songinfo', songid, permanent=True)

def songinfo_downvote(request, songid):
    song_instance = Song.objects.get(pk=songid)

    object, created = Song_rating.objects.get_or_create(
        user_id=request.user,
        song_id=song_instance)
    if created: # If new, assign time right now and save.
        object.date = datetime.now().utcnow().date()
        object.rating_type = False
        object.save()
    else: # If not new
        if object.rating_type: # if its a upvote already, change it to be an upvote.
            object.rating_type = False
            object.date = datetime.now().utcnow().date()
            object.save()
        else: # User is pressing upvote button when it was already pressed, get rid of upvote.
            object.delete()
    return redirect('songinfo', songid, permanent=True)

def playlist_upvote(request, playlistid):
    playlist_instance = Playlist.objects.get(pk=playlistid)

    object, created = Playlist_rating.objects.get_or_create(
        user_id=request.user,
        playlist_id=playlist_instance)
    if created: # If new, assign time right now and save.
        object.date = datetime.now().utcnow().date()
        object.rating_type = True
        object.save()
    else: # If not new
        if not object.rating_type: # if its a downvote already, change it to be an upvote.
            object.rating_type = True
            object.date = datetime.now().utcnow().date()
            object.save()
        else: # User is pressing upvote button when it was already pressed, get rid of upvote.
            object.delete()
    return redirect('addsongs_view', playlistid, permanent=True)

def playlist_downvote(request, playlistid):
    playlist_instance = Playlist.objects.get(pk=playlistid)

    object, created = Playlist_rating.objects.get_or_create(
        user_id=request.user,
        playlist_id=playlist_instance)
    if created: # If new, assign time right now and save.
        object.date = datetime.now().utcnow().date()
        object.rating_type = False
        object.save()
    else: # If not new
        if object.rating_type: # if its a downvote already, change it to be an upvote.
            object.rating_type = False
            object.date = datetime.now().utcnow().date()
            object.save()
        else: # User is pressing upvote button when it was already pressed, get rid of upvote.
            object.delete()
    return redirect('addsongs_view', playlistid, permanent=True)


def settings_general(request):
    # Do not allow anonymous users to go to settings. Redirect to login.
    if not request.user.is_authenticated:
        return redirect('login', permanent=True)

    if request.method == 'POST':

        id_darkmode = request.POST.get('dark_mode')
        id_explicit = request.POST.get('explicit')

        if id_darkmode == 'on':
            User_Setting_Ext.objects.filter(user=request.user).update(dark_mode=True)
        else:
            User_Setting_Ext.objects.filter(user=request.user).update(dark_mode=False)

        if id_explicit == 'on':
            User_Setting_Ext.objects.filter(user=request.user).update(explicit=True)
        else:
            User_Setting_Ext.objects.filter(user=request.user).update(explicit=False)

    return render(request, 'settings_general.html', {})

def settings_security(request):
    # Do not allow anonymous users to go to settings. Redirect to login.
    if not request.user.is_authenticated:
        return redirect('login', permanent=True)
    return render(request, 'settings_security.html')

def settings_reset_password(request):
    # Do not allow anonymous users to go to settings. Redirect to login.
    if not request.user.is_authenticated:
        return redirect('login', permanent=True)

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
    # Do not allow anonymous users to go to settings. Redirect to login.
    if not request.user.is_authenticated:
        return redirect('login', permanent=True)

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
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, 'Account was created for ' + username)

            #Create appropriate rows in our user tables.
            User_Setting_Ext.objects.create( # defaults
                user=user,
                dark_mode=False,
                explicit=False
            )

            return redirect('home')


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
    return render(request, 'topcharts.html')

def topChart_post(request, region_name):
    region_id = region_codes[region_name] # from dictionary in file region_codes.py

    songs_json = sp.playlist(region_id)

    final_songs_list = []

    songs_json = songs_json["tracks"]
    for json_obj in songs_json["items"]:
        print(json.dumps(json_obj))
        json_obj = json_obj["track"]
        album_json = json_obj["album"] # album json object
        album_id = album_json["id"] # track's album id

        album_artists = []
        for artist_obj in json_obj["artists"]:
            album_artists.append(artist_obj['name'])
        album_artists_str = ", ".join(album_artists)

        track_info = {
            "id" : json_obj["id"],
            "name" : json_obj["name"],
            "number" : json_obj["track_number"],
            "explicit" : json_obj["explicit"],
            "artists" : album_artists_str,
            "album_id" : album_id,
            "album_name" : album_json["name"],
            "album_release_date" : album_json["release_date"],
            "album_cover" : album_json["images"][2]["url"]
            # IN "album_cover", change to 0 for bigger pic, 2 for smaller pic
        }

        # If it is in a compilation, we just flat out ignore it and don't show it.
        if album_json["album_type"] != 'compilation':
            final_songs_list.append(track_info)

    context  = {'region': region_id, 'region_name': region_name, "songs": final_songs_list}
    print (region_id)
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
    not_same_user = False
    already_friends = False
    self = None
    try:
        self = User.objects.get(pk=request.user.id)
        if user != self:
            not_same_user = True
        else:
            not_same_user = False
        already_friends = Friend.objects.are_friends(request.user, user)
    except:
        pass # False values already set

    allfriends = Friend.objects.friends(user)
    saved_playlists = User_Profile.objects.filter(user=user_id)
    playlists = Playlist.objects.filter(user_id=user_id)
    song_ratings = Song_rating.objects.filter(user_id=user_id, date__gte=datetime.now().date() - timedelta(days=7))
    album_ratings = Album_rating.objects.filter(user_id=user_id, date__gte=datetime.now().date() - timedelta(days=7))
    playlist_ratings = Playlist_rating.objects.filter(user_id=user_id, date__gte=datetime.now().date() - timedelta(days=7))


    # Used for checking if these two users have  requested each other already, and pass this to template.
    request_information = {
        "request_from_them": False,
        "request_to_them": False
    }
    # Very ugly: checks if a request is available and changes dict accordingly.
    # Is then passed to template to let it know what button to show.
    try:
        FriendshipRequest.objects.get(from_user=user, to_user=request.user)
        request_information["request_from_them"] = True
    except:
        pass

    try:
        FriendshipRequest.objects.get(from_user=request.user, to_user=user)
        request_information["request_to_them"] = True
    except:
        pass

    #print(request.user, user)
    return render(request, 'events/show_user.html', {'user_to_show': user, 'allfriends':allfriends,
                                                     'not_same_user':not_same_user, 'self':self,
                                                     'already_friends':already_friends, 'saved_playlists': saved_playlists,
                                                     'playlists': playlists, 'song_ratings': song_ratings, 'album_ratings': album_ratings,
                                                     'playlist_ratings': playlist_ratings, 'request_info': request_information})


def addFriend(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    added = Friend.objects.add_friend(self,user)

    print("You :" , self, "Added: " , user, "Were they added:" , added)
    # duplicate code because I don't get why it wont redirect properly
    not_same_user = False
    already_friends = False
    self = None
    try:
        self = User.objects.get(pk=request.user.id)
        if user != self:
            not_same_user = True
        else:
            not_same_user = False
        already_friends = Friend.objects.are_friends(request.user, user)
    except:
        pass # False values already set

    allfriends = Friend.objects.friends(user)
    saved_playlists = User_Profile.objects.filter(user=user_id)
    playlists = Playlist.objects.filter(user_id=user_id)

    # Used for checking if these two users have  requested each other already, and pass this to template.
    request_information = {
        "request_from_them": False,
        "request_to_them": False
    }
    # Very ugly: checks if a request is available and changes dict accordingly.
    # Is then passed to template to let it know what button to show.
    try:
        FriendshipRequest.objects.get(from_user=user, to_user=request.user)
        request_information["request_from_them"] = True
    except:
        pass

    try:
        FriendshipRequest.objects.get(from_user=request.user, to_user=user)
        request_information["request_to_them"] = True
    except:
        pass

    #print(request.user, user)
    return render(request, 'events/show_user.html', {'user_to_show': user, 'allfriends':allfriends,
                                                     'not_same_user':not_same_user, 'self':self,
                                                     'already_friends':already_friends, 'saved_playlists': saved_playlists, 'playlists': playlists,
                                                     'request_info': request_information})

def accept_friend_request_profile(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    friend_request = FriendshipRequest.objects.get(from_user=user, to_user=self)
    friend_request.accept()
    # duplicate code because I don't get why it wont redirect properly
    not_same_user = False
    already_friends = False
    self = None
    try:
        self = User.objects.get(pk=request.user.id)
        if user != self:
            not_same_user = True
        else:
            not_same_user = False
        already_friends = Friend.objects.are_friends(request.user, user)
    except:
        pass # False values already set

    allfriends = Friend.objects.friends(user)
    saved_playlists = User_Profile.objects.filter(user=user_id)
    playlists = Playlist.objects.filter(user_id=user_id)

    #print(request.user, user)
    return render(request, 'events/show_user.html', {'user_to_show': user, 'allfriends':allfriends,
                                                     'not_same_user':not_same_user, 'self':self,
                                                     'already_friends':already_friends, 'saved_playlists': saved_playlists, 'playlists': playlists})


def deleteFriend(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    removed = Friend.objects.remove_friend(user, self)
    print("You :" , self, "Removed: " , user, "Were they removed:" , removed)
    # duplicate code because I don't get why it wont redirect properly
    not_same_user = False
    already_friends = False
    self = None
    try:
        self = User.objects.get(pk=request.user.id)
        if user != self:
            not_same_user = True
        else:
            not_same_user = False
        already_friends = Friend.objects.are_friends(request.user, user)
    except:
        pass # False values already set

    allfriends = Friend.objects.friends(user)
    saved_playlists = User_Profile.objects.filter(user=user_id)
    playlists = Playlist.objects.filter(user_id=user_id)

    #print(request.user, user)
    return render(request, 'events/show_user.html', {'user_to_show': user, 'allfriends':allfriends,
                                                     'not_same_user':not_same_user, 'self':self,
                                                     'already_friends':already_friends, 'saved_playlists': saved_playlists, 'playlists': playlists})

def blockFriend(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    blocked = Block.objects.add_block(self, user)
    removed = Friend.objects.remove_friend(user, self)
    print("You :" , self, "Blocked: " , user , blocked)
    return render(request, 'events/block_user.html', {'user':user, 'self':self, 'blocked':blocked})

def unblockFriend(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    unblocked = Block.objects.remove_block(self, user)
    print("You :" , self, "Unblocked: " , user , unblocked)
    return render(request, 'events/unblock_user.html', {'user':user, 'self':self, 'unblocked':unblocked})

def notifications(request):
    # Do not allow anonymous users to go to settings. Redirect to login.
    if not request.user.is_authenticated:
        return redirect('login', permanent=True)

    incoming_requests = Friend.objects.unread_requests(user=request.user)

    return render(request, 'notifications.html', {"current_user": request.user,
    "incoming_requests": incoming_requests})

def accept_friend_request_notifications(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    friend_request = FriendshipRequest.objects.get(from_user=user, to_user=self)
    friend_request.accept()

    incoming_requests = FriendshipRequest.objects.filter(to_user=request.user)

    return render(request, 'notifications.html', {"current_user": request.user,
    "incoming_requests": incoming_requests})

def reject_friend_request_notifications(request, user_id):
    user = User.objects.get(pk=user_id)
    self = User.objects.get(pk=request.user.id)
    friend_request = FriendshipRequest.objects.get(from_user=user, to_user=self)
    friend_request.delete()

    incoming_requests = FriendshipRequest.objects.filter(to_user=request.user)

    return render(request, 'notifications.html', {"current_user": request.user,
    "incoming_requests": incoming_requests})

def delete(request, comment_id, next=None):
    """
    Deletes a comment. Confirmation on GET, action on POST. Requires the "can
    moderate comments" permission.
    Templates: :template:`comments/delete.html`,
    Context:
        comment
            the flagged `comments.comment` object
    """
    comment = get_object_or_404(django_comments.get_model(),
                                pk=comment_id,
                                site__pk=get_current_site(request).pk)

    # Delete on POST
    if request.method == 'POST':
        # Flag the comment as deleted instead of actually deleting it.
        #perform_delete(request, comment)
        comment.delete()
        return next_redirect(request, fallback=next or 'comments-delete-done',
                             c=comment.pk)

    # Render a form on GET
    else:
        return render(request, 'comments/delete.html', {'comment': comment, "next": next})
