# /workspace/shiftwise/accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm, AgencySignUpForm
from shifts.models import ShiftAssignment
from django.utils import timezone

User = get_user_model()

@login_required
def profile_view(request):
    """
    Renders the profile page for the logged-in user.
    """
    user = request.user
    assignments = ShiftAssignment.objects.filter(worker=user).select_related('shift').order_by('shift__shift_date')
    upcoming_shifts = [assignment.shift for assignment in assignments if assignment.shift.shift_date >= timezone.now().date()]
    past_shifts = [assignment.shift for assignment in assignments if assignment.shift.shift_date < timezone.now().date()]

    context = {
        'user': user,
        'upcoming_shifts': upcoming_shifts,
        'past_shifts': past_shifts,
    }
    return render(request, 'accounts/profile.html', context)

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
            return redirect(reverse('accounts:profile'))
        else:
            messages.error(request, "Invalid username or password.")
            return redirect(reverse('accounts:login_view'))

    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    """
    Logs out the current user and redirects to the home page.
    """
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect(reverse('home:home'))

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
            return redirect(reverse('accounts:profile'))
        else:
            messages.error(request, "There was a problem with your signup details.")
    else:
        form = SignUpForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/signup.html', context)

def agency_signup_view(request):
    """
    Handles the agency signup process.
    """
    if request.method == 'POST':
        form = AgencySignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your agency account has been created.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "There was a problem with your signup details.")
    else:
        form = AgencySignUpForm()
    return render(request, 'accounts/agency_signup.html', {'form': form})
