from django import forms
from .models import Playlist
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SongForm(forms.Form):
    song_name = forms.CharField(widget=forms.TextInput(attrs={"size": "50"}))

class PlaylistForm(forms.ModelForm):
    class Meta:
        model= Playlist
        fields= ["name"]
        labels = {
            'name': '',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Playlist Name'})
        }

class EditUserForm(forms.ModelForm):

      class Meta:
        model = User
        fields = (
          'first_name',
          'last_name',
          'username',
          'email',
        )

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class SearchByUserID(forms.ModelForm):
    class Meta:
        model= User
        fields= ["id"]
        labels = {
            'name': 'Search by user id',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search For User ID'})
        }

class ProfileForm(forms.Form):
    user_name = forms.CharField(widget=forms.TextInput(attrs={"size": "50"}))
