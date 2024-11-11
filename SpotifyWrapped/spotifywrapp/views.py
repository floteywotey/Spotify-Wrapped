import os
import requests
from .forms import CreateInvite
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

def readings(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    return render(request, 'readings.html', {"recent" : recentWraps(request.user.username)})

def home(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    recent = recentWraps(request.user.username)
    sortedArray = ['','','']
    if (recent):
        count = 0
        for wrap in recent:
            if (count < 3):
                sortedArray[count] = wrap
                count = count + 1
    return render(request, 'home.html', {'recent':sortedArray})

def userlogin(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('startscreen')

def deleteQuestion(request):
    return render(request, 'delete?.html', {})

def deleteUser(request):
    if request.method == 'POST':
        user = request.user
        for item in SpotifyUser.objects.filter(user=request.user.username):
            item.delete()
        user.delete()
    return render(request, 'delete..html', {})

# Home Page (Before spotify authorization login)
def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            spot = SpotifyUser.objects.create(user=user.username, spotifytoken="", refreshtoken='')
            spot.save()
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = CreateInvite(request.POST)
        if form.is_valid():
            invite = form.save()
            invite.userFrom = request.user.username
            invite.save()
            return redirect('profile')
    else:
        form = CreateInvite()
    inviteList = list(invites.objects.filter(userTo=request.user.username))
    return render(request, 'profile.html', {'form' : form, 'usertoken' : getSpotifyUser(request.user.username).spotifytoken, 'inviteList' : inviteList})

def select_date(request):
    return render(request, 'selectDateScreen.html')

def results(request):
    sortedArray = recentWraps(request.user.username)
    return render(request, 'results.html', context={'wrap': sortedArray[0]})

def solo_results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == "POST":
        time = request.POST.get('time', '')
        data = getSoloWrap(request, request.user.username, time, 50)
        wrap = wraps.objects.create(wrap1=data, wrap2={}, duowrap={}, isDuo=False, user1=request.user.username)
        wrap.save()
        return redirect('results')
    return redirect('results')

def duo_results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == "POST":
        time = request.POST.get('time', '')
        invite = request.POST.get('id', '')
        fromUser = request.POST.get('fromUser', '')
        toUser = request.user.username
        wrapData1 = getSoloWrap(request, fromUser, time, 50)
        wrapData2 = getSoloWrap(request, toUser, time, 50)

        shared_artists = []
        shared_genres = []
        shared_tracks = []
        shared_albums = []

        for artist1 in wrapData1['top_artists']:
            for artist2 in wrapData2['top_artists']:
                if artist1 == artist2:
                    shared_artists.append(artist1)

        for genre1 in wrapData1['top_genres']:
            for genre2 in wrapData2['top_genres']:
                if genre1 == genre2:
                    shared_genres.append(genre1)

        for track1 in wrapData1['top_tracks']:
            for track2 in wrapData2['top_tracks']:
                if track1 == track2:
                    shared_tracks.append(track1)

        for album1 in wrapData1['top_albums']:
            for album2 in wrapData2['top_albums']:
                if album1 == album2:
                    shared_albums.append(album1)

        shared_danceability = (wrapData1['danceability'] + wrapData2['danceability'])/2
        shared_popularity = (wrapData1['popularity'] + wrapData2['popularity'])/2
        shared_energy = (wrapData1['energy'] + wrapData2['energy'])/2
        shared_valence = (wrapData1['valence'] + wrapData2['valence'])/2

        data = {
            'top_artists': shared_artists,
            'top_genres': shared_genres,
            'top_tracks': shared_tracks,
            'top_albums': shared_albums,
            'danceability': shared_danceability,
            'popularity': shared_popularity,
            'energy': shared_energy,
            'valence': shared_valence
        }
        invites.objects.filter(id=invite).delete()
        wrap = wraps.objects.create(wrap1=wrapData1, wrap2=wrapData2, duowrap=data, isDuo=True, user1=fromUser, user2=request.user.username)
        wrap.save()
        return redirect('results')
    return redirect('results')

def getUserToken(username):
    return getSpotifyUser(username).getspotifytoken()

def refreshToken(request, username):
    user = list(SpotifyUser.objects.filter(user=username))[0]
    spotifyToken = user.getspotifytoken()
    refresh = user.getrefreshtoken()
    if not spotifyToken:
        spotify_authorize(request)
    else:
        token_url = 'https://accounts.spotify.com/api/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            user.spotifytoken = tokens['access_token']
            if 'refresh_token' in tokens:
                user.refreshtoken = tokens['refresh_token']
            user.save()
        else:
            print(f"Error refreshing token: {response.status_code}")

def get_top_tracks(request, token, time, username, limit=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': limit, 'time_range': time}

    response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers, params=params)
    if response.status_code == 401:
        refreshToken(request, username)
        headers = {'Authorization': f'Bearer {getSpotifyUser(username).getspotifytoken()}'}
        response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top artists! Status code: {response.status_code}")
    return response.json()

def get_top_artists(request, token, time, username, limit=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': limit, 'time_range': time}

    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
    if response.status_code == 401:
        refreshToken(request, username)
        headers = {'Authorization': f'Bearer {getSpotifyUser(username).getspotifytoken()}'}
        response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top artists! Status code: {response.status_code}")
    return response.json()

def recentWraps(username):
    unsortedArray = list(wraps.objects.filter(user1=username)) + list(
        wraps.objects.filter(user2=username))
    sortedArray = sorted(
        unsortedArray,
        key=lambda x: x.getdate(), reverse=True
    )
    return sortedArray

def getSpotifyUser(username):
    return list(SpotifyUser.objects.filter(user=username))[0]

def getSoloWrap(request, username, time, limit=10):
    danceability = 0.0
    popularity = 0.0
    energy = 0.0
    valence = 0.0
    songcsv = ''
    user =  list(SpotifyUser.objects.filter(user=username))[0]
    #try:
    token = user.getspotifytoken() # Retrieve token from session
    if not token:
        spotify_authorize(request)
    # Get top artists and extract genres
    top_artists = get_top_artists(request, token, time, username, limit)
    artist_dict = []
    for artist in top_artists['items']:
        dict = {
            'image' : artist['images'][0]['url'],
            'name' : artist['name'],
            'id' : artist['id'],
        }
        artist_dict.append(dict)
    genres = {}
    for artist in top_artists['items']:
        for genre in artist['genres']:
            genres[genre] = genres.get(genre, 0) + 1
    sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)

    user = list(SpotifyUser.objects.filter(user=username))[0]
    token = user.getspotifytoken()
    # Get top tracks and extract albums
    top_tracks = get_top_tracks(request, token, time, username, limit)
    track_dict = []
    for track in top_tracks['items']:
        dict = {
            'id' : track['id'],
            'image' : track['album']['images'][0]['url'],
            'popularity' : track['popularity'],
        }
        track_dict.append(dict)
    albums = {}
    for track in top_tracks['items']:
        popularity += track['popularity']
        album = track['album']['name']
        songcsv += str(track['id']) + ','
        albums[album] = albums.get(album, 0) + 1
    sorted_albums = sorted(albums.items(), key=lambda x: x[1], reverse=True)

    # Using previous tracks, grab danceability, energy, valence, and popularity and take average
    headers = {'Authorization': f'Bearer {token}'}
    params = {'ids': songcsv}
    response = requests.get('https://api.spotify.com/v1/audio-features', headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch top tracks! Status code: {response.status_code}")
    print(len(response.json()['audio_features']))
    for item in response.json()['audio_features']:
        for track in track_dict:
            if track['id'] == item['id']:
                track['valence'] = item['valence']
                track['energy'] = item['energy']
                track['danceability'] = item['danceability']
        valence += item['valence']
        danceability += item['danceability']
        energy += item['energy']
    danceability /= limit
    popularity /= limit
    energy /= limit
    valence /= limit
    sorted_popularity = sorted(track_dict, key=lambda x: x['popularity'], reverse=True)
    sorted_valence = sorted(track_dict, key=lambda x: x['valence'], reverse=True)
    sorted_energy = sorted(track_dict, key=lambda x: x['energy'], reverse=True)
    sorted_danceability = sorted(track_dict, key=lambda x: x['danceability'], reverse=True)
    # Prepare data for response
    data = {
        'top_artists': artist_dict[:5],
        'top_genres': [genre[0] for genre in sorted_genres][:5],
        'top_genre': [genre[0] for genre in sorted_genres][:1],
        'num_genres' : len(sorted_genres),
        'top_tracks': track_dict[:5],
        'top_albums': [album[0] for album in sorted_albums],
        'sorted_danceability' : sorted_danceability[:3],
        'sorted_valence' : sorted_valence[:3],
        'sorted_energy' : sorted_energy[:3],
        'sorted_popularity' : sorted_popularity[:3],
        'danceability': danceability,
        'popularity': popularity,
        'energy': energy,
        'valence': valence
    }
    return data
    #except Exception as e:
        #return JsonResponse({'error': str(e)}, status=500)

# Redirect user for Spotify authorization
def spotify_authorize(request):
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
                item.refreshtoken = token_info['refresh_token']
                item.save()
            # Redirect to the view that fetches user data
            return redirect('profile')
        else:
            # Handle missing access token in the response
            return JsonResponse({'error': 'Access token not found in the response'}, status=500)
    else:
        # Handle the case where the request to Spotify's token endpoint failed
        return JsonResponse({'error': 'Failed to get the access token from Spotify'}, status=response.status_code)
