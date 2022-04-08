import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from .cashe_handler import DatabaseTokenHandler
from numpy.random import default_rng
from .models import Song, Album
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

def get_saved_tracks(client):
    '''
    takes in a client object with user account permissions
    gets a users top tracks
    '''

    tracks = client.current_user_saved_tracks()['items']
    indexs = rng.choice(range(len(tracks)), size=5, replace=False)
    track_urls = []
    for index in indexs:
        track_urls.append(tracks[index]['track']['href'])

    return track_urls

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

def gen_recomendations(client):
    '''
    returns a list of recommended playlists, also puts the albums into database objects
    '''

    seed_tracks = get_saved_tracks(client)
    album_list = []

    for item in client.recommendations(seed_genres=[], seed_tracks=seed_tracks)['tracks']:
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
