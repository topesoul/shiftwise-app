from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Shift

def shift_list(request):
    shifts = Shift.objects.all()
    return render(request, 'shifts/shift_list.html', {'shifts': shifts})
