from django import forms
from django.contrib.auth.models import User
from ratemypet.models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('picture', 'about',)