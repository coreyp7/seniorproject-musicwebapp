from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

# Create your views here.
import spotipy
from cashe_handler import DatabaseTokenHandler
from numpy.random import default_rng

scope = 'user-library-read'

def link_account(request):

    if str(request.user) != 'AnonymousUser' and ( user := User.objects.get(pk=int(request.user.id)) ):

        cache_handler = DatabaseTokenHandler(user)
        auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scope,
        cache_handler=cache_handler)

        if request.GET.get('code'):
            token = auth_manager.parse_response_code(request.build_absolute_uri())
            token_info = auth_manager.get_access_token(token)
            cache_handler.save_token_to_cache(token_info)
            return redirect('/')

        elif not auth_manager.validate_token(cache_handler.get_cached_token()):
            auth_url = auth_manager.get_authorize_url()
            return redirect(auth_url)

    return redirect('/')
