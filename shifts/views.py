from django.shortcuts import render, redirect
from .forms import ShiftForm
from .models import Shift

def shift_list(request):
    shifts = Shift.objects.all()
    return render(request, 'shifts/shift_list.html', {'shifts': shifts})

def shift_create(request):
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shift_list')
    else:
        form = ShiftForm()
    return render(request, 'shifts/shift_form.html', {'form': form})

def shift_update(request, pk):
    shift = Shift.objects.get(pk=pk)
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('shift_list')
    else:
        form = ShiftForm(instance=shift)
    return render(request, 'shifts/shift_form.html', {'form': form})
