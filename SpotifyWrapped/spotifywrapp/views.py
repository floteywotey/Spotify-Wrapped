import os
import requests
import base64

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from dotenv import load_dotenv
from django.http import JsonResponse
from django.http import HttpResponse


#loads environment variables from .env, so client id and secret client etc
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")


#Spotify Token URL
AUTH_URL = 'https://accounts.spotify.com/api/token'

def startscreen(request):
    error_message = None
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('spotify_authorize')
    return render(request, 'login.html', {'form': form, 'error_message': error_message})

# Home Page (Before spotify authorization login)
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('startscreen')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


# Redirect user for Spotify authorization
def spotify_authorize(request):
    scope = 'user-top-read'
    auth_url = (
        'https://accounts.spotify.com/authorize?'
        f'client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={scope}'
    )
    return redirect(auth_url)

def spotify_callback(request):
    code = request.GET.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(token_url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        token_info = response.json()  # Get the token information
        # Ensure access token is present in the response
        if 'access_token' in token_info:
            # Store the access token in the session
            request.session['spotify_access_token'] = token_info['access_token']
            # Redirect to the view that fetches user data
            return redirect('spotify_data')
        else:
            # Handle missing access token in the response
            return JsonResponse({'error': 'Access token not found in the response'}, status=500)
    else:
        # Handle the case where the request to Spotify's token endpoint failed
        return JsonResponse({'error': 'Failed to get the access token from Spotify'}, status=response.status_code)

def get_top_artists(token, limit=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': limit, 'time_range': 'medium_term'}

    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top artists! Status code: {response.status_code}")
    return response.json()

def get_top_tracks(token, limit=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': limit, 'time_range': 'medium_term'}

    response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top tracks! Status code: {response.status_code}")
    return response.json()

def spotify_data(request):
    try:
        token = request.session.get('spotify_access_token')  # Retrieve token from session
        if not token:
            return JsonResponse({'error': 'No access token found, please authorize again.'}, status=401)

        # Get top artists and extract genres
        top_artists = get_top_artists(token)
        genres = {}
        for artist in top_artists['items']:
            for genre in artist['genres']:
                genres[genre] = genres.get(genre, 0) + 1
        sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)

        # Get top tracks and extract albums
        top_tracks = get_top_tracks(token)
        albums = {}
        for track in top_tracks['items']:
            album = track['album']['name']
            albums[album] = albums.get(album, 0) + 1
        sorted_albums = sorted(albums.items(), key=lambda x: x[1], reverse=True)

        # Prepare data for response
        data = {
            'top_artists': [artist['name'] for artist in top_artists['items']],
            'top_genres': [genre[0] for genre in sorted_genres],
            'top_tracks': [track['name'] for track in top_tracks['items']],
            'top_albums': [album[0] for album in sorted_albums]
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)