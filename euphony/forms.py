from django import forms
from .models import Playlist, UserGroup
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import User_Setting_Ext

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

class EditGeneralForm(forms.ModelForm):

      class Meta:
        model = User_Setting_Ext
        fields = (
          'dark_mode',
          'explicit',
        )

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class PostForm(forms.ModelForm):
    class Meta:
        fields = ("message", "group")
        model = models.Post

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["group"].queryset = (
                models.Group.objects.filter(
                    pk__in=user.groups.values_list("group__pk")
                )
            )
