#App-Level urls.py

from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.startscreen, name='startscreen'),
    path("register/", views.register, name='register'),
    path("login/", views.userlogin, name='login'),
    path("spotify-authorize/", views.spotify_authorize, name='spotify_authorize'),
    path("spotify-callback/", views.spotify_callback, name='spotify_callback'),
    path("spotify-data/", views.spotify_data, name='spotify_data'),
    path("home/", views.home, name='home'),
]