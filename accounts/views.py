from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def logout_view(request):
    return render(request, 'accounts/logout.html')

def signup_view(request):
    return render(request, 'accounts/signup.html')
