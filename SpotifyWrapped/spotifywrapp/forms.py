from django import forms
from . import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
User._meta.get_field('email')._unique = True
class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'email', 'password1', 'password2']:
            self.fields[fieldname].help_text = None


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
        required=False,
    )

    class Meta:
        model = models.invites
        fields = ['userTo', 'time', 'message']
