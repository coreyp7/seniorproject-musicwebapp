import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from .cashe_handler import DatabaseTokenHandler
from numpy.random import default_rng
from .models import Song, Album, UserToken
import json

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

rng = default_rng()

def gen_client(user, scope):
    '''
    takes in a user object, and a scope string
    returns a client object that can access that users spotify account
    if a user hasn't linked a spotify account this function returns None
    '''

    cache_handler = DatabaseTokenHandler(user)
    if cache_handler.get_cached_token() != "":
        auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scope,
        cache_handler=cache_handler)
        temp_client = spotipy.Spotify(auth_manager=auth_manager)
        return temp_client
    else:
        return None

def get_friend_saved_tracks(freinds, scope):
    '''
    takes in a list of users filters out the non linked accounts
    and returns a list of song ids from the friends
    '''

    friends_with_tokens = []
    songs = []

    for friend in freinds:
        try:
            friends_with_tokens.append(UserToken.objects.get(user=friend.id))
        except UserToken.DoesNotExist:
            pass



    for friend in friends_with_tokens:
        client = gen_client(friend, scope)
        tracks = client.current_user_saved_tracks()['items']

    songs.extend(tracks)

    return songs


def gen_seed(client, friends, scope):
    '''
    takes in a client object with user account permissions
    gets a users top tracks, or top artist to make a recommendation seed
    '''

    seeds = [[],[],[]]


    my_tracks = client.current_user_saved_tracks()['items']
    friends_tracks = get_friend_saved_tracks(friends, scope)

    if len(my_tracks) > 0:
        rng.shuffle(list(my_tracks))
        rng.shuffle(list(friends_tracks))

        seed_tracks = my_tracks[:3]
        seed_tracks.extend(friends_tracks[:2])

        track_urls = []
        for track in seed_tracks:
            track_urls.append(track['track']['href'])

        seeds[2] = track_urls

    else:
        #artist_urls = []
        #artists = client.current_user_top_artists(limit=5)['items']

        #for artist in artists:
        #    artist_urls.append(artist['href'])

        seeds[1] = ['anime']

    return seeds

def insert_songs(album_id, song_id):
    pass


def get_song_list(client, album_list):
    '''
    upon getting a list of albums get the song objects in the albums from spotify
    '''

    songs_list = []

    for album in album_list:
        for track in client.album_tracks(album.id)['items']:


            object, created = Song.objects.get_or_create(id=track['id'],
                                                               album_id=album,
                                                               name=track['name'],
                                                               artists=track['artists'][0],
                                                               duration_ms=track['duration_ms'],
                                                               explicit = track['explicit'],
                                                               release_date = album.release_date,
                                                               track_number = track['track_number'],
                                                               disc = track['disc_number'],
                                                               allow_comments=True)

            songs_list.append(object)

    return songs_list

def gen_recomendations(client, friends, scope):
    '''
    returns a list of recommended playlists, also puts the albums into database objects
    '''

    seeds = gen_seed(client, friends, scope)

    album_list = []
    for item in client.recommendations(seed_artists=seeds[0], seed_genres=seeds[1], seed_tracks=seeds[2])['tracks']:
        object, created = Album.objects.get_or_create(
                                                    id=item['album']["id"],
                                                    defaults = {
                                                    "name"  : item["name"],
                                                    "artists" : item["artists"][0], #TEMPORARY
                                                    "release_date" : item['album']["release_date"],
                                                    "total_tracks" : item['album']["total_tracks"],
                                                    "cover" : item["album"]["images"][1]["url"]
                                                    }
                                                    )

        album_list.append(object)

    return album_list

# Function for adding all of the songs of a specified album to our db.
# album_json is a specific dictionary:
"""
album_json = {
    "id" : "spotify id of album",
    "name" : "name of album",
    "release_date" : "",
    "type" : "",
    "total_tracks" : "",
    "artists" : ["This", "will", "be", "a", "list"],
    "cover" : "This will be a link"
    }
    """
# album_model_obj is the object reference of the album.
#       This is required to easily set the 1toMany field in each Song row. You receive this obj when using 'get_or_create' in dbs.
# (This is required to set the one to many field in Song)
def add_albums_songs(album_json, album_model_obj):
    album_tracks = sp.album_tracks(album_json["id"])
    #print(json.dumps(album_tracks, indent=4))
    #print(json.dumps(album_json))
    album_tracks = album_tracks["items"]

    for json_obj in album_tracks:
        # track stuff
        track_id = json_obj["id"]
        track_name = json_obj["name"]
        track_number = json_obj["track_number"] # track's placement in album
        track_explicit = json_obj["explicit"] # track's explicitity
        track_artists = json_obj["artists"]

        track_artists = []
        for artist_obj in track_artists:
            track_artists.append(artist_obj['name'])
        track_artists_str = ", ".join(track_artists)

        track_info = {
            "id" : track_id,
            "name" : track_name,
            "number" : track_number,
            "disc" : json_obj["disc_number"],
            "explicit" : track_explicit,
            "artists" : track_artists_str,
            "release_date" : album_json["release_date"]
        }

        object, created = Song.objects.get_or_create(
            id=track_info["id"],
            defaults = {
            "name" : track_info["name"],
            "artists" : track_info["artists"],
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

# Currently only used in album_info function in views.py.
# Converts ms runtime of album to formatted string of runtime.
# Putting here since it might be helpful later.
def convertMillis(millis):

    seconds=(millis/1000)%60
    minutes=(millis/(1000*60))%60
    hours=(millis/(1000*60*60))%24

    hours = str.split(str(hours), '.')[0]
    minutes = str.split(str(minutes), '.')[0]
    seconds = str.split(str(seconds), '.')[0]

    if int(seconds)<10:
        seconds = f"0{seconds}"

    """
    if int(minutes)<10:
        minutes = f"0{minutes}"
    """

    final_string = ""

    if int(hours) == 0 and int(minutes) == 0:
        final_string = f"0:{seconds}"
    elif int(hours) == 0:
        final_string = f"{minutes}:{seconds}"
    else:
        if int(minutes)<10:
            minutes = f"0{minutes}"
        final_string = f"{hours}:{minutes}:{seconds}"

    return final_string
