from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class SpotifyUser(models.Model):
    user = models.CharField(max_length=150)
    spotifytoken = models.CharField(max_length=100)
    nexttoken = models.CharField(max_length=100)
    def __str__(self):
        return str(self.user)

class Friends(models.Model):
    user1 = models.CharField(max_length=150)
    user2 = models.CharField(max_length=150)

class friendRequests(models.Model):
    userFrom = models.CharField(max_length=150)
    userTo = models.CharField(max_length=150)
    message = models.CharField(max_length=150)

class invites(models.Model):
    userFrom = models.CharField(max_length=150)
    userTo = models.CharField(max_length=150)
    message = models.CharField(max_length=150)

class wraps(models.Model):
    wrap1 = models.JSONField()
    wrap2 = models.JSONField()
    duowrap = models.JSONField()
    isDuo = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)
    user1 = models.CharField(max_length=150)
    user2 = models.CharField(max_length=150)
    def getdate(self):
        return self.date


