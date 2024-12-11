from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Book


class UserRegistrationForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'password',
            'required': 'required',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'required': 'required',
            'id': 'confirm_password'
        })
    )

    class Meta:
        model = User
        fields = ['fullname', 'email', 'phone_number', 'password1', 'password2']
        widgets = {
            'fullname': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'required': 'required',
                'id': 'fullname'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'required': 'required',
                'id': 'email'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'phone_number',
                'required': 'required',
                'type': 'tel'  # Changed from number to tel for better mobile experience
            }),
        }

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'genre', 'isbn', 'publisher',
            'price', 'cover_image', 'stock', 'published_date', 'pages'
        ]

        widgets = {
            'published_date': forms.DateInput(attrs={'type': 'date'}),
        }
