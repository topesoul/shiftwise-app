from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .forms import ShiftForm
from .models import Shift, ShiftAssignment
from .utils import get_address_from_postcode


# Shift List View
class ShiftListView(LoginRequiredMixin, ListView):
    model = Shift
    template_name = 'shifts/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('shift_date', 'start_time')
        if self.request.user.is_superuser:
            return queryset  # Superusers can see all shifts
        if hasattr(self.request.user, 'profile') and self.request.user.profile.agency:
            return queryset.filter(agency=self.request.user.profile.agency)
        return Shift.objects.none()  # If user has no agency


# Custom Mixin for Agency Validation
class AgencyMixin(UserPassesTestMixin):
    def test_func(self):
        shift = self.get_object()
        return shift.agency == self.request.user.profile.agency


# Shift Create View
class ShiftCreateView(LoginRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shifts:shift_list')

    def form_valid(self, form):
        form.instance.agency = self.request.user.profile.agency
        postcode = form.cleaned_data['postcode']
        address_data = get_address_from_postcode(postcode)

        if address_data:
            form.instance.address_line1 = address_data['address_line1']
            form.instance.city = address_data['city']
            form.instance.state = address_data.get('county', '')
            form.instance.country = address_data.get('country', 'UK')
            form.instance.latitude = address_data['latitude']
            form.instance.longitude = address_data['longitude']
        else:
            messages.error(self.request, "Could not fetch address for the provided postcode.")
            return self.form_invalid(form)

        messages.success(self.request, "Shift created successfully.")
        return super().form_valid(form)


# Shift Update View with Agency Validation
class ShiftUpdateView(LoginRequiredMixin, AgencyMixin, UpdateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shifts:shift_list')

    def form_valid(self, form):
        # Fetch updated address details based on postcode
        postcode = form.cleaned_data['postcode']
        address_data = get_address_from_postcode(postcode)

        if address_data:
            form.instance.address_line1 = address_data['address_line1']
            form.instance.city = address_data['city']
            form.instance.state = address_data.get('county', '')
            form.instance.country = address_data.get('country', 'UK')
            form.instance.latitude = address_data['latitude']
            form.instance.longitude = address_data['longitude']
        else:
            messages.error(self.request, "Could not fetch address for the provided postcode.")
            return self.form_invalid(form)

        messages.success(self.request, "Shift updated successfully.")
        return super().form_valid(form)


# Shift Delete View with Date Validation
class ShiftDeleteView(LoginRequiredMixin, AgencyMixin, DeleteView):
    model = Shift
    template_name = 'shifts/shift_confirm_delete.html'
    success_url = reverse_lazy('shifts:shift_list')

    def delete(self, request, *args, **kwargs):
        shift = self.get_object()
        if shift.shift_date < timezone.now().date():
            messages.error(request, "Cannot delete a past shift.")
            return HttpResponseRedirect(self.success_url)
        messages.success(self.request, f'Shift "{shift.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Shift Booking Function
@login_required
def book_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)

    # Ensure user is from the same agency
    if shift.agency != request.user.profile.agency:
        messages.error(request, "You cannot book shifts from another agency.")
        return redirect('shifts:shift_list')

    if shift.shift_date < timezone.now().date():
        messages.error(request, "You cannot book a shift that is in the past.")
        return redirect('shifts:shift_list')

    if shift.is_full:
        messages.error(request, "This shift is already fully booked.")
        return redirect('shifts:shift_list')

    if ShiftAssignment.objects.filter(worker=request.user, shift=shift).exists():
        messages.error(request, "You are already assigned to this shift.")
        return redirect('shifts:shift_list')

    ShiftAssignment.objects.create(worker=request.user, shift=shift)
    messages.success(request, "You have successfully booked this shift.")
    return redirect('shifts:shift_list')
