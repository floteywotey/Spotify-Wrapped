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
    path("readings/", views.readings, name='readings'),
    path("solo-results/", views.solo_results, name='solo_results'),
    path("select-date/", views.select_date, name='select_date'),
    path("delete/", views.deleteUser, name='delete'),
    path("delete?/", views.deleteQuestion, name='delete?'),
    path("profile/", views.profile, name='profile'),
    path("duo-results/", views.duo_results, name='duo_results'),
    path("results/", views.results, name='results'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='custom_password_reset'),
    path('password-reset-done/', views.CustomPasswordResetDoneView.as_view(), name='custom_password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='custom_password_reset_confirm'),
    path('password-reset-complete/', views.CustomPasswordResetCompleteView.as_view(), name='custom_password_reset_complete'),
]