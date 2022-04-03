import spotipy
from .cashe_handler import DatabaseTokenHandler
from numpy.random import default_rng
from .models import Song, Album

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
                                                               artist=track['artists'][0],
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
                                                    "artist" : item["artists"][0], #TEMPORARY
                                                    "release_date" : item['album']["release_date"],
                                                    "total_tracks" : item['album']["total_tracks"],
                                                    "cover" : item["album"]["images"][1]["url"]
                                                    }
                                                    )

        album_list.append(object)

    return album_list