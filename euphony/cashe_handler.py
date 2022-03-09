import spotipy
from account_link.models import UserToken
import json

class DatabaseTokenHandler(spotipy.cache_handler.CacheHandler):

    def __init__(self, user):
        self.user = user

    def get_cached_token(self):

        try:

            token_object = UserToken.objects.get(user=self.user)
            token_object = json.loads(token_object.token.replace("'",'"'))

        except:

            token_object = ""

        return token_object

    def save_token_to_cache(self, token_info):
        token_object = UserToken(user=self.user, token=token_info)
        token_object.save()
        return None
