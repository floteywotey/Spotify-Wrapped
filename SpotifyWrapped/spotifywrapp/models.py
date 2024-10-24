from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class User(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spotifytoken = models.CharField(max_length=100)
    def __str__(self):
        return str(self.user.username)

class Friends(models.Model):
    user1 = models.CharField(max_length=150)
    user2 = models.CharField(max_length=150)

class invites(models.Model):
    userFrom = models.CharField(max_length=150)
    userTo = models.CharField(max_length=150)
    message = models.CharField(max_length=150)

class wraps(models.Model):
    energy = models.DecimalField(max_digits=10, decimal_places=9)
    danceability = models.DecimalField(max_digits=10, decimal_places=9)
    speechiness = models.DecimalField(max_digits=10, decimal_places=9)
    valence = models.DecimalField(max_digits=10, decimal_places=9)

    user1 = models.CharField(max_length=150)
    user2 = models.CharField(max_length=150)

