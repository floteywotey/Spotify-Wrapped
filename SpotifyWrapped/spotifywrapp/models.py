from django.db import models
#import uuid
from django.contrib.auth.models import User
# Create your models here.

class SpotifyUser(models.Model):
    user = models.CharField(max_length=150)
    spotifytoken = models.CharField(max_length=100)
    refreshtoken = models.CharField(max_length=100)
    def __str__(self):
        return str(self.user)
    def getspotifytoken(self):
        return self.spotifytoken
    def getrefreshtoken(self):
        return self.refreshtoken

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
    longTerm = "long_term"
    medTerm = "medium_term"
    shortTerm = "short_term"
    choices = [
        (longTerm, "long_term"),
        (medTerm, "medium_term"),
        (shortTerm, "short_term"),
    ]
    time = models.CharField(
        max_length=15,
        choices=choices
    )
    message = models.CharField(max_length=150)
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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


