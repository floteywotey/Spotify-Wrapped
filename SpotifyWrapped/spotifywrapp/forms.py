from django import forms
from . import models
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import SpotifyUser


## User Creation Form

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter a valid email address.")

    class Meta:
        model = SpotifyUser
        fields = ("user", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class CreateInvite(forms.ModelForm):

    userTo = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter username'}),
        required=True,
    )

    longTerm = "long_term"
    medTerm = "medium_term"
    shortTerm = "short_term"
    choices = [
        (longTerm, "long term"),
        (medTerm, "medium term"),
        (shortTerm, "short term"),
    ]

    time = forms.ChoiceField(
        choices=choices,
        widget=forms.RadioSelect(),
        required=True,
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Message'}),
        required=True,
    )

    class Meta:
        model = models.invites
        fields = ['userTo', 'time', 'message']
