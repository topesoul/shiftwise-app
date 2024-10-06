from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def custom_login(request):
    return render(request, 'accounts/login.html')

def custom_signup(request):
    return render(request, 'accounts/signup.html')

def profile(request):
    return render(request, 'accounts/profile.html')
