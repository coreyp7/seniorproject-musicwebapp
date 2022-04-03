from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from numpy.random import default_rng
import json

from .cashe_handler import DatabaseTokenHandler
from .forms import SongForm

from .models import User_Setting_Ext

from django.contrib import messages
from .forms import EditUserForm, EditGeneralForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

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
        args = {'form': form,}
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

def topChart_post(request):
    context  = {}
    return render(request, 'topcharts.html', context)
