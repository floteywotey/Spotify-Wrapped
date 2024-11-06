from django import forms
from . import models
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

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
