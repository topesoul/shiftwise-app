from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .forms import ShiftForm
from .models import Shift, ShiftAssignment
from .utils import get_address_from_postcode

# Shift List View
class ShiftListView(ListView):
    model = Shift
    template_name = 'shifts/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('shift_date', 'start_time')
        if self.request.user.is_superuser:
            return queryset  # Superusers can see all shifts
        # Restrict agency admins to only their agency's shifts
        return queryset.filter(agency=self.request.user.profile.agency)


# Shift Create View
class ShiftCreateView(CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shift_list')

    def form_valid(self, form):
        # Automatically set the agency based on the logged-in user's profile
        form.instance.agency = self.request.user.profile.agency

        # Fetch address details based on postcode
        postcode = form.cleaned_data['postcode']
        address_data = get_address_from_postcode(postcode)
        
        if address_data:
            # Populate the form with the retrieved address details
            form.instance.address_line1 = address_data['address_line1']
            form.instance.city = address_data['city']
            form.instance.county = address_data.get('county', '')
            form.instance.country = address_data.get('country', 'UK')
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
        # Ensure the shift belongs to the user's agency
        if form.instance.agency != self.request.user.profile.agency:
            messages.error(self.request, "You can only update shifts from your own agency.")
            return redirect('shift_list')

        # Fetch address details based on postcode if it has been changed
        postcode = form.cleaned_data['postcode']
        address_data = get_address_from_postcode(postcode)
        
        if address_data:
            # Update the form with the retrieved address details
            form.instance.address_line1 = address_data['address_line1']
            form.instance.city = address_data['city']
            form.instance.county = address_data.get('county', '')
            form.instance.country = address_data.get('country', 'UK')
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

    def get(self, request, *args, **kwargs):
        shift = self.get_object()
        # Prevent deletion if the shift is already booked or has passed
        if shift.shift_date < timezone.now().date():
            messages.error(request, "Cannot delete a past shift.")
            return HttpResponseRedirect(self.success_url)
        return super().get(request, *args, **kwargs)


# Shift Booking Function
def book_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)

    # Check if the shift belongs to the user's agency
    if shift.agency != request.user.profile.agency:
        messages.error(request, "You cannot book shifts from another agency.")
        return redirect('shift_list')

    # Prevent booking past shifts
    if shift.shift_date < timezone.now().date():
        messages.error(request, "You cannot book a shift that is in the past.")
        return redirect('shift_list')

    # Check if the shift is already full
    if shift.is_full:
        messages.error(request, "This shift is already fully booked.")
        return redirect('shift_list')

    # Prevent duplicate assignment
    if ShiftAssignment.objects.filter(worker=request.user, shift=shift).exists():
        messages.error(request, "You are already assigned to this shift.")
        return redirect('shift_list')

    # Create the assignment
    ShiftAssignment.objects.create(worker=request.user, shift=shift)
    messages.success(request, "You have successfully booked this shift.")
    return redirect('shift_list')