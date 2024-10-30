#App-Level urls.py

from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.startscreen, name='startscreen'),
    path("register/", views.register, name='register'),
    path("login/", views.userlogin, name='login'),
    path("logout/", views.logout_view, name='logout'),
    path("spotify-authorize/", views.spotify_authorize, name='spotify_authorize'),
    path("spotify-unauthorize/", views.spotify_unauthorize, name='spotify_unauthorize'),
    path("spotify-callback/", views.spotify_callback, name='spotify_callback'),
    path("home/", views.home, name='home'),
    path("results/", views.results, name='results'),
    path("select-date/", views.select_date, name='select_date'),
    path("delete/", views.deleteUser, name='delete'),
    path("profile/", views.profile, name='profile'),
]