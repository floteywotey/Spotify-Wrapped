import os
from random import randint

import requests
from .forms import CreateInvite, SignUpForm
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from dotenv import load_dotenv
from django.http import JsonResponse

from .models import SpotifyUser, wraps, invites
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
User._meta.get_field('email')._unique = True
#loads environment variables from .env, so client id and secret client etc
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI_HOME = os.getenv("SPOTIFY_REDIRECT_URI_HOME")
REDIRECT_URI_PROFILE = os.getenv("SPOTIFY_REDIRECT_URI_PROFILE")

#Spotify Token URL
AUTH_URL = 'https://accounts.spotify.com/api/token'


def startscreen(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'startscreen.html')

def readings(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == 'POST':
        identity = request.POST.get('id', '')
        print(identity)
        wrap = wraps.objects.get(id=identity)
        print(wrap)
        if (wrap.user1 == request.user.username):
            wrap.user1 = ''
        if (wrap.user2 == request.user.username):
            wrap.user2 = ''
        wrap.save()
    return render(request, 'readings.html', {"recent" : recentWraps(request.user.username)})

def home(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    recent = recentWraps(request.user.username)
    sortedArray = []
    if (recent):
        count = 0
        for wrap in recent:
            if (count < 3):
                sortedArray.append(wrap)
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
    if not request.user.is_authenticated:
        return redirect('startscreen')
    return render(request, 'delete?.html', {})

def deleteUser(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == 'POST':
        user = request.user
        for item in SpotifyUser.objects.filter(user=request.user.username):
            item.delete()
        for item in wraps.objects.filter(user1=request.user.username):
            item.user1 = ''
            item.save()
        for item in wraps.objects.filter(user2=request.user.username):
            item.user2 = ''
            item.save()
        for item in invites.objects.filter(userTo=request.user.username):
            item.delete()
        for item in invites.objects.filter(userFrom=request.user.username):
            item.delete()
        user.delete()
    return render(request, 'delete..html', {})

# Home Page (Before spotify authorization login)
def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            spot = SpotifyUser.objects.create(user=user.username, spotifytoken="", refreshtoken='')
            spot.save()
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = CreateInvite(request.POST)
        if form.is_valid():
            invite = form.save()
            invite.userFrom = request.user.username
            invite.fromSpotifyToken = SpotifyUser.objects.get(user=request.user.username).spotifytoken
            invite.fromRefreshToken = SpotifyUser.objects.get(user=request.user.username).refreshtoken
            if not SpotifyUser.objects.filter(user=invite.userTo).exists():
                invite.delete()
            invite.save()
            return redirect('profile')
    else:
        form = CreateInvite()
    inviteList = list(invites.objects.filter(userTo=request.user.username))
    return render(request, 'profile.html', {'username' : request.user.username, 'form' : form, 'usertoken' : getSpotifyUser(request.user.username).spotifytoken, 'inviteList' : inviteList})

def select_date(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if SpotifyUser.objects.get(user=request.user.username).spotifytoken == '':
        return redirect('spotify_authorize_home')
    return render(request, 'selectDateScreen.html')

def results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    sortedArray = recentWraps(request.user.username)
    return render(request, 'results.html', context={'wrap': sortedArray[0]})

def post_results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    identity = request.POST.get('id', '')
    wrap = wraps.objects.get(id=identity)
    return render(request, 'results.html', context={'wrap': wrap})

def solo_results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == "POST":
        time = request.POST.get('time', '')
        data = getSoloWrap(request, request.user.username, time, 50)

        randInt = randint(0,13)
        if (len(recentWraps(request.user.username)) > 0):
            while (randInt == recentWraps(request.user.username)[0].imageNum):
                randInt = randint(0,13)
        wrap = wraps.objects.create(wrap1=data, wrap2={}, duowrap={}, isDuo=False, user1=request.user.username, imageNum = randInt, image = imageList[randInt])
        wrap.save()
        return redirect('results')
    return redirect('results')

def duo_results(request):
    if not request.user.is_authenticated:
        return redirect('startscreen')
    if request.method == "POST":
        if SpotifyUser.objects.get(user=request.user.username).spotifytoken == '':
            return redirect('spotify_authorize_profile')
        time = request.POST.get('time', '')
        invite = request.POST.get('id', '')
        print(invite)
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
            'numSharedArtists': len(shared_artists),
            'numSharedGenres': len(shared_genres),
            'numSharedTracks': len(shared_tracks),
            'numSharedAlbums': len(shared_albums),
            'danceability': shared_danceability,
            'popularity': shared_popularity,
            'energy': shared_energy,
            'valence': shared_valence
        }
        invites.objects.filter(id=invite).delete()
        randInt = randint(0, 13)
        if (len(recentWraps(fromUser)) > 0 and len(recentWraps(toUser)) > 0):
            while (randInt == recentWraps(fromUser)[0].imageNum or randInt == recentWraps(toUser)[0].imageNum):
                randInt = randint(0, 13)
        elif (len(recentWraps(fromUser)) > 0):
            while (randInt == recentWraps(fromUser)[0].imageNum):
                randInt = randint(0, 13)
        elif (len(recentWraps(toUser)) > 0):
            while (randInt == recentWraps(toUser)[0].imageNum):
                randInt = randint(0, 13)
        wrap = wraps.objects.create(wrap1=wrapData1, wrap2=wrapData2, duowrap=data, isDuo=True, user1=fromUser, user2=request.user.username, imageNum = randInt, image = imageList[randInt])
        wrap.save()
        return redirect('results')
    return redirect('results')

def getUserToken(username):
    return getSpotifyUser(username).getspotifytoken()

def refreshToken(request, username):
    user = list(SpotifyUser.objects.filter(user=username))[0]
    print('aaaaaa')
    spotifyToken = user.getspotifytoken()
    refresh = user.getrefreshtoken()
    if not spotifyToken:
        return spotify_authorize_home(request)
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
    token = user.spotifytoken # Retrieve token from session

    # Get top artists and extract genres
    top_artists = get_top_artists(request, token, time, username, limit)
    artist_dict = []
    for artist in top_artists['items']:
        if (len(artist.get('images')) == 0):
            image = 'N/A'
        else:
            image = artist.get('images', [{'url': 'None'}])[0].get('url', 'None')
        dict = {
            'image' : image,
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
        artists = ''
        for artist in track['artists']:
            artists += artist['name'] + ','
        artists = artists[:-1]
        print(artists)
        dict = {
            'id' : track['id'],
            'name' : track['name'],
            'image' : track['album'].get('images', [{'url':'None'}])[0].get('url','None'),
            'popularity' : track['popularity'],
            'artists' : artists,
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
    for item in response.json()['audio_features']:
        for track in track_dict:
            if track['id'] == item['id']:
                track['valence'] = item['valence'] * 100
                track['energy'] = item['energy'] * 100
                track['danceability'] = item['danceability'] * 100
        valence += item['valence'] * 100
        danceability += item['danceability'] * 100
        energy += item['energy'] * 100
    danceability /= limit
    popularity /= limit
    energy /= limit
    valence /= limit
    danceability = round(danceability, 2)
    energy = round(energy, 2)
    popularity = round(popularity, 2)
    valence = round(valence, 2)
    top_popularity = sorted(track_dict, key=lambda x: x['popularity'], reverse=True)
    top_valence = sorted(track_dict, key=lambda x: x['valence'], reverse=True)
    top_energy = sorted(track_dict, key=lambda x: x['energy'], reverse=True)
    top_danceability = sorted(track_dict, key=lambda x: x['danceability'], reverse=True)
    bot_popularity = sorted(track_dict, key=lambda x: x['popularity'], reverse=False)
    bot_valence = sorted(track_dict, key=lambda x: x['valence'], reverse=False)
    bot_energy = sorted(track_dict, key=lambda x: x['energy'], reverse=False)
    bot_danceability = sorted(track_dict, key=lambda x: x['danceability'], reverse=False)
    # Prepare data for response
    data = {
        'top5artists': artist_dict[:5],
        'top5genres': [genre[0] for genre in sorted_genres][:5],
        'topgenre': [genre[0] for genre in sorted_genres][:1],
        'top_artists': artist_dict,
        'top_genres' : [genre[0] for genre in sorted_genres],
        'num_genres' : len(sorted_genres),
        'top5tracks': track_dict[:5],
        'top_tracks' : track_dict,
        'top_albums': [album[0] for album in sorted_albums],
        'top3danceability' : top_danceability[:3],
        'top3valence' : top_valence[:3],
        'top3energy' : top_energy[:3],
        'top3popularity' : top_popularity[:3],
        'bot3danceability' : bot_danceability[:3],
        'bot3valence' : bot_valence[:3],
        'bot3energy' : bot_energy[:3],
        'bot3popularity' : bot_popularity[:3],
        'danceability': danceability,
        'popularity': popularity,
        'energy': energy,
        'valence': valence
    }
    return data
    #except Exception as e:
        #return JsonResponse({'error': str(e)}, status=500)

# Redirect user for Spotify authorization
def spotify_authorize_profile(request):
    scope = 'user-top-read'
    URI = REDIRECT_URI_PROFILE
    auth_url = (
        'https://accounts.spotify.com/authorize?'
        f'client_id={CLIENT_ID}&response_type=code&redirect_uri={URI}&scope={scope}&show_dialog=true'
    )
    return redirect(auth_url)

def spotify_unauthorize(request):
    for item in SpotifyUser.objects.filter(user=request.user.username):
        item.spotifytoken = ''
        item.save()
    return redirect('profile')

def spotify_callback_profile(request):
    code = request.GET.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI_PROFILE,
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

def spotify_authorize_home(request):
    scope = 'user-top-read'
    URI = REDIRECT_URI_HOME
    auth_url = (
        'https://accounts.spotify.com/authorize?'
        f'client_id={CLIENT_ID}&response_type=code&redirect_uri={URI}&scope={scope}&show_dialog=true'
    )
    return redirect(auth_url)

def spotify_callback_home(request):
    code = request.GET.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI_HOME,
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
            return redirect('home')
        else:
            # Handle missing access token in the response
            return JsonResponse({'error': 'Access token not found in the response'}, status=500)
    else:
        # Handle the case where the request to Spotify's token endpoint failed
        return JsonResponse({'error': 'Failed to get the access token from Spotify'}, status=response.status_code)

def password_reset(request):
    if request.method == 'POST':
        password_form = PasswordResetForm(request.POST)
        if password_form.is_valid():
            data = password_form.cleaned_data['email']
            user_email = User.objects.filter(Q(email=data))
            if user_email.exists():
                for user in user_email:
                    subject = 'Password Request'
                    email_template_name = 'password_message.txt'
                    parameters = {
                        'email':user.email,
                        'username':user.username,
                        'domain': '127.0.0.1:8000',
                        'site_name': 'Spotify',
                        'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                        'token' : default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, parameters)
                    send_mail(subject, email, 'spotifywrapped19@gmail.com', [user.email], fail_silently=False)
                    return redirect('password_reset_done')
    else:
        password_form = PasswordResetForm()
    context = {
        'form': password_form,
    }
    return render(request, 'password_reset_form.html', context)

imageList = [
            '/static/SpotifyWrapped/images/card/card_fronts_notext/reawakening-dark.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/reawakening-light.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-alchemist.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-bard.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-chariot.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-explorer.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-hermit.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-jester.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-lovers.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-moon.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-rogue.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-scholar.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-sun.svg',
            '/static/SpotifyWrapped/images/card/card_fronts_notext/the-wizard.svg'
]