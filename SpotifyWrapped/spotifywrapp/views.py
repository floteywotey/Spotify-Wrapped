import os
import requests

from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from dotenv import load_dotenv
from django.http import JsonResponse

from .models import SpotifyUser, wraps, invites


#loads environment variables from .env, so client id and secret client etc
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


#Spotify Token URL
AUTH_URL = 'https://accounts.spotify.com/api/token'

def startscreen(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'startscreen.html')

def home(request):
    unsortedArray = list(wraps.objects.filter(user1=request.user.username)) + list(
        wraps.objects.filter(user2=request.user.username))
    sortedArray = sorted(
        unsortedArray,
        key=lambda x: x.getdate(), reverse=True
    )
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if (list(SpotifyUser.objects.filter(user=request.user.username))[0].spotifytoken == ''):
        spotify_authorize(request)
    return render(request, 'home.html', {'recent':sortedArray})

def userlogin(request):
    if request.user.is_authenticated:
        return redirect('home')
    error_message = None
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'error_message': error_message})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('startscreen')

def deleteUser(request):
    if request.method == 'POST':
        user = request.user
        for item in SpotifyUser.objects.filter(user=request.user.username):
            item.delete()
        user.delete()
    return redirect('startscreen')

# Home Page (Before spotify authorization login)
def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            spot = SpotifyUser.objects.create(user=user.username, spotifytoken="")
            spot.save()
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'profile.html', {'usertoken' : list(SpotifyUser.objects.filter(user=request.user.username))[0].spotifytoken})


# Redirect user for Spotify authorization
def spotify_authorize(request):
    if not request.user.is_authenticated:
        print('bbbbb')
    scope = 'user-top-read'
    auth_url = (
        'https://accounts.spotify.com/authorize?'
        f'client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={scope}&show_dialog=true'
    )
    return redirect(auth_url)

def spotify_unauthorize(request):
    for item in SpotifyUser.objects.filter(user=request.user.username):
        item.spotifytoken = ''
        item.save()
    return redirect('profile')

def spotify_callback(request):
    if not request.user.is_authenticated:
        print('aaaaa')
    code = request.GET.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    response = requests.post(token_url, data=data)
    # Check if the request was successful
    if response.status_code == 200:
        token_info = response.json()  # Get the token information
        # Ensure access token is present in the response
        if 'access_token' in token_info:
            # Store the access token in the session
            for item in SpotifyUser.objects.filter(user=request.user.username):
                item.spotifytoken = token_info['access_token']
                item.nexttoken = token_info['refresh_token']
                item.save()
            # Redirect to the view that fetches user data
            return redirect('profile')
        else:
            # Handle missing access token in the response
            return JsonResponse({'error': 'Access token not found in the response'}, status=500)
    else:
        # Handle the case where the request to Spotify's token endpoint failed
        return JsonResponse({'error': 'Failed to get the access token from Spotify'}, status=response.status_code)


def get_top_artists(token, time, limit=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': limit, 'time_range': time}

    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
    if response.status_code == 401:
        token_url = 'https://accounts.spotify.com/api/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': list(SpotifyUser.objects.filter(user=request.user.username))[0].getrefreshtoken(),
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_info = response.json()  # Get the token information
            # Ensure access token is present in the response
            if 'access_token' in token_info:
                # Store the access token in the session
                for item in SpotifyUser.objects.filter(user=request.user.username):
                    item.spotifytoken = token_info['access_token']
                    item.nexttoken = token_info['refresh_token']
                    item.save()
                headers = {'Authorization': f'Bearer {token_info['access_token']}'}
                params = {'limit': limit, 'time_range': time}

                response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
            else:
                # Handle missing access token in the response
                return JsonResponse({'error': 'Access token not found in the response'}, status=500)
        else:
            # Handle the case where the request to Spotify's token endpoint failed
            return JsonResponse({'error': 'Failed to get the access token from Spotify'}, status=response.status_code)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top artists! Status code: {response.status_code}")
    return response.json()

def get_top_tracks(token, time, limit=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': limit, 'time_range': time}

    response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers, params=params)
    if response.status_code == 401:
        token_url = 'https://accounts.spotify.com/api/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': list(SpotifyUser.objects.filter(user=request.user.username))[0].getrefreshtoken(),
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_info = response.json()  # Get the token information
            # Ensure access token is present in the response
            if 'access_token' in token_info:
                # Store the access token in the session
                for item in SpotifyUser.objects.filter(user=request.user.username):
                    item.spotifytoken = token_info['access_token']
                    item.nexttoken = token_info['refresh_token']
                    item.save()
                headers = {'Authorization': f'Bearer {token_info['access_token']}'}
                params = {'limit': limit, 'time_range': time}

                response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers, params=params)
            else:
                # Handle missing access token in the response
                return JsonResponse({'error': 'Access token not found in the response'}, status=500)
        else:
            # Handle the case where the request to Spotify's token endpoint failed
            return JsonResponse({'error': 'Failed to get the access token from Spotify'}, status=response.status_code)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top artists! Status code: {response.status_code}")
    return response.json()

def select_date(request):
    return render(request, 'selectDateScreen.html')

def solo_results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == "POST":
        time = request.POST.get('time', '')
        danceability = 0.0
        popularity = 0.0
        energy = 0.0
        valence = 0.0
        songcsv = ''

        try:
            token = list(SpotifyUser.objects.filter(user=request.user.username))[0].spotifytoken  # Retrieve token from session
            if not token:
                return JsonResponse({'error': 'No access token found, please authorize again.'}, status=401)


            # Get top artists and extract genres
            top_artists = get_top_artists(token, time)
            genres = {}
            for artist in top_artists['items']:
                for genre in artist['genres']:
                    genres[genre] = genres.get(genre, 0) + 1
            sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)

            # Get top tracks and extract albums
            top_tracks = get_top_tracks(token, time)
            albums = {}
            for track in top_tracks['items']:
                popularity += track['popularity']
                album = track['album']['name']
                songcsv += str(track['id']) + ','
                albums[album] = albums.get(album, 0) + 1
            sorted_albums = sorted(albums.items(), key=lambda x: x[1], reverse=True)

            # Using previous tracks, grab danceability, energy, valence, and popularity and take average
            # (assumes 10 items)
            headers = {'Authorization': f'Bearer {token}'}
            params = {'ids': songcsv}

            response = requests.get('https://api.spotify.com/v1/audio-features', headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch top tracks! Status code: {response.status_code}")
            for item in response.json()['audio_features']:
                valence += item['valence']
                danceability += item['danceability']
                energy += item['energy']
            danceability /= 10.0
            popularity /= 10.0
            energy /= 10.0
            valence /= 10.0

            # Prepare data for response
            data = {
                'top_artists': [artist['name'] for artist in top_artists['items']],
                'top_genres': [genre[0] for genre in sorted_genres],
                'top_tracks': [track['name'] for track in top_tracks['items']],
                'top_albums': [album[0] for album in sorted_albums],
                'danceability' : danceability,
                'popularity' : popularity,
                'energy' : energy,
                'valence' : valence
            }
            wrap = wraps.objects.create(wrap1=data, wrap2 = {}, duowrap = {}, isDuo=False, user1=request.user.username)
            wrap.save()
            redirect('solo_results')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        unsortedArray = list(wraps.objects.filter(user1=request.user.username)) + list(
            wraps.objects.filter(user2=request.user.username))
        sortedArray = sorted(
            unsortedArray,
            key=lambda x: x.getdate(), reverse=True
        )
    return render(request, 'results.html', context={'wrap':sortedArray[0]})
