from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def custom_login(request):
    # Point to the allauth login template
    return render(request, 'allauth/account/login.html')

def custom_signup(request):
    # Point to the allauth signup template
    return render(request, 'allauth/account/signup.html')

# For custom profile template
def profile(request):
    return render(request, 'accounts/profile.html')
