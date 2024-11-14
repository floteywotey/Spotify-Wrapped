#App-Level urls.py

from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.startscreen, name='startscreen'),
    path("register/", views.register, name='register'),
    path("login/", views.userlogin, name='login'),
    path("logout/", views.logout_view, name='logout'),
    path("spotify-authorize-home/", views.spotify_authorize_home, name='spotify_authorize_home'),
    path("spotify-unauthorize/", views.spotify_unauthorize, name='spotify_unauthorize'),
    path("spotify-callback-home/", views.spotify_callback_home, name='spotify_callback_home'),
    path("spotify-authorize-profile/", views.spotify_authorize_profile, name='spotify_authorize_profile'),
    path("spotify-callback-profile/", views.spotify_callback_profile, name='spotify_callback_profile'),
    path("home/", views.home, name='home'),
    path("readings/", views.readings, name='readings'),
    path("solo-results/", views.solo_results, name='solo_results'),
    path("select-date/", views.select_date, name='select_date'),
    path("delete/", views.deleteUser, name='delete'),
    path("delete?/", views.deleteQuestion, name='delete?'),
    path("profile/", views.profile, name='profile'),
    path("duo-results/", views.duo_results, name='duo_results'),
    path("results/", views.results, name='results'),
]