from spotifywrapp.models import SpotifyUser
from spotifywrapp.views import getSpotifyUser

def theme_preference(request):
    if request.user.is_authenticated and request.user.is_active:
        spotify_user = getSpotifyUser(request.user.username)
        if spotify_user:  # check if instance exists
            return {'theme_preference': spotify_user.get_theme_preference()}
    return {'theme_preference': 'dark'}  # default to 'dark' if no user or preference found
