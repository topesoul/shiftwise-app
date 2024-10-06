from django.shortcuts import render

# Create your views here.
# accounts/views.py
def custom_login(request):
    return render(request, 'allauth/account/login.html')

def custom_signup(request):
    return render(request, 'allauth/account/signup.html')


def profile(request):
    return render(request, 'accounts/profile.html')
