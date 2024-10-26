from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", startscreen, name='startscreen'),
    path("register/", register, name='register'),
    path("spotify_authorize/", spotify_authorize, name='spotify_authorize'),
    path("spotify_callback/", spotify_callback, name='spotify_callback'),
    path("home/", home, name='home'),
]