from django import forms
from .models import Playlist

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
