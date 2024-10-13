from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm

# Profile view: Accessible only to authenticated users
@login_required
def profile_view(request):
    """
    Renders the profile page for the logged-in user.
    """
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)

# Login view: Uses built-in Django authentication
def login_view(request):
    """
    Handles the login process. Redirects to profile page after successful login.
    """
    if request.method == 'POST':
        # Retrieve form data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(reverse('account_profile'))
        else:
            messages.error(request, "Invalid username or password.")
            return redirect(reverse('account_login'))

    return render(request, 'accounts/login.html')

# Logout view: Logs out the user and redirects to home page
@login_required
def logout_view(request):
    """
    Logs out the current user and redirects to the home page.
    """
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect(reverse('home'))

# Signup view: Handles user registration
def signup_view(request):
    """
    Handles the user signup process. Creates a new user and logs them in.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log in the user after successful signup
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect(reverse('account_profile'))
        else:
            messages.error(request, "There was a problem with your signup details.")
    else:
        form = SignUpForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/signup.html', context)