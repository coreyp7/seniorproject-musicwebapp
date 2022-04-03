from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import User_Setting_Ext


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


class ProfileForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
