from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from .forms import ShiftForm
from .models import Shift
from .utils import get_address_from_postcode

# Shift List View
class ShiftListView(ListView):
    model = Shift
    template_name = 'shifts/shift_list.html'
    context_object_name = 'shifts'

# Shift Create View
class ShiftCreateView(CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shift_list')

    def form_valid(self, form):
        # Fetch address details based on postcode
        postcode = form.cleaned_data['postcode']
        address_data = get_address_from_postcode(postcode)
        
        if address_data:
            # Populate the form with the retrieved address details
            form.instance.address_line1 = address_data['address_line1']
            form.instance.city = address_data['city']
            form.instance.county = address_data['county']
            form.instance.country = address_data['country']
            form.instance.latitude = address_data['latitude']
            form.instance.longitude = address_data['longitude']
        else:
            messages.error(self.request, "Could not fetch address for the provided postcode.")
            return self.form_invalid(form)

        messages.success(self.request, "Shift created successfully.")
        return super().form_valid(form)

# Shift Update View
class ShiftUpdateView(UpdateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shift_list')

    def form_valid(self, form):
        # Fetch address details based on postcode if it has been changed
        postcode = form.cleaned_data['postcode']
        address_data = get_address_from_postcode(postcode)
        
        if address_data:
            # Update the form with the retrieved address details
            form.instance.address_line1 = address_data['address_line1']
            form.instance.city = address_data['city']
            form.instance.county = address_data['county']
            form.instance.country = address_data['country']
            form.instance.latitude = address_data['latitude']
            form.instance.longitude = address_data['longitude']
        else:
            messages.error(self.request, "Could not fetch address for the provided postcode.")
            return self.form_invalid(form)

        messages.success(self.request, "Shift updated successfully.")
        return super().form_valid(form)

# Shift Delete View
class ShiftDeleteView(DeleteView):
    model = Shift
    template_name = 'shifts/shift_confirm_delete.html'
    success_url = reverse_lazy('shift_list')

    def delete(self, request, *args, **kwargs):
        shift = self.get_object()
        messages.success(self.request, f'Shift "{shift.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)