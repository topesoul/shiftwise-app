from django.shortcuts import render
from django.utils import timezone

def home_view(request):
    """
    Renders the homepage.
    """
    return render(request, 'home/home.html')
