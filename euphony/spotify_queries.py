import spotipy
from .cashe_handler import DatabaseTokenHandler
from numpy.random import default_rng

rng = default_rng()

def gen_client(user, scope):
    '''
    takes in a user object, and a scope string
    returns a client object that can access that users spotify account
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


def get_song_id_list(client, album_id_list):
    '''
    upon getting a list of albums get the songs in the albums from spotify
    '''

    id_list = []

    for id in album_id_list:
        for track in client.album_tracks(id)['items']:
            #print(track)
            id_list.append(track['id'])

    return id_list

def gen_recomendations(client):
    '''
    returns a list of recommended playlists
    '''
    seed_tracks = get_saved_tracks(client)
    id_list = []

    for item in client.recommendations(seed_genres=[], seed_tracks=seed_tracks)['tracks']:

        '''
        album.objects.get_or_create(id=item['album']['id'],
                                     album_type=item['album']['album_type'],
                                     name=item['album']['name'],
                                     release_date=item['album']['release_date'],
                                     total_tracks=int(item['album']['total_tracks']))

        '''
        id_list.append(item['album']['id'])

    return id_list
