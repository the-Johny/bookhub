from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import render, redirect

from bookapp.forms import UserRegistrationForm
from bookapp.models import User


# Create your views here.

def index(request):
    return render(request, 'index.html')


def featured_books(request):
    return render(request, 'featured_books.html')


def popular(request):
    return render(request, 'popular.html')


def offers(request):
    return render(request, 'offers.html')


def articles(request):
    return render(request, 'articles.html')


def is_admin(user):
    """Check if a user is authenticated and an admin."""
    return user.is_authenticated and user.role == 'ADMIN'


def user_register(request):
    """Handle user registration."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            # Check for duplicate email
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.", extra_tags="register_error")
            else:
                form.save()
                messages.success(request, "Registered successfully! Please log in.", extra_tags="register_success")
                return redirect('login')  # Redirect to login after successful registration
        else:
            messages.error(request, "Please fix the input errors below.", extra_tags="register_error")
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    """Handle user login."""
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!', extra_tags="login_success")

            # Redirect based on user role
            if user.role == 'ADMIN':
                return redirect('admin-home')  # Redirect to admin home
            elif user.role == 'USER':
                return redirect('user-home')  # Redirect to user home
            else:
                return redirect('index')  # Default redirect (e.g., for guests or other roles)
        else:
            messages.error(request, 'Invalid email or password.', extra_tags="login_error")

    return render(request, 'login.html')


def user_logout(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, "You have been logged out successfully.", extra_tags="logout_success")
    return redirect('login')
