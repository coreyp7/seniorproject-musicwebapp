from django import forms
from django.contrib.auth.models import User

class SongForm(forms.Form):
    song_name = forms.CharField(widget=forms.TextInput(attrs={"size": "50"}))

class EditUserForm(forms.ModelForm):

      class Meta:
        model = User
        fields = (
          'first_name',
          'last_name',
          'username',
          'email',
        )

