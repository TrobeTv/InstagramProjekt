# core/forms.py
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile
from .models import Post
from django import forms
from django.contrib.auth.models import User
from .models import Comment

class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Uživatelské jméno'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    password1 = forms.CharField(
        label="Heslo",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Heslo'
        })
    )
    password2 = forms.CharField(
        label="Potvrď heslo",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Heslo znovu'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'autofocus': True, 'placeholder': 'Uživatelské jméno'}))
    password = forms.CharField(label="Heslo", strip=False, widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Heslo'}))

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'dark_mode']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'O tobě'}),
            'dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'caption': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Popisek…',
            }),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Přidejte komentář…'
            })
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'avatar')


class MessageForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Napište zprávu…'
        }),
        label='' # Skryjeme label, placeholder je dostatečný
    )