from spotifywrapp.models import SpotifyUser
from spotifywrapp.views import getSpotifyUser

def theme_preference(request):
    if request.user.is_authenticated:
        try:
            spotify_user = getSpotifyUser(request.user.username)
            return {'theme_preference': spotify_user.get_theme_preference()}
        except SpotifyUser.DoesNotExist:
            pass
    return {'theme_preference': 'dark'}  # Default to 'dark' if not logged in or no preference found
