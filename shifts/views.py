from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView
)
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin
)
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test
)
from django.views.decorators.http import require_GET
from django.core.exceptions import PermissionDenied
from .forms import ShiftForm
from .models import Shift, ShiftAssignment
from .utils import get_address_from_postcode
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Custom Mixins for Permission Handling

class AgencyManagerRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure that the user is part of the 'Agency Managers' group.
    Only Agency Managers can perform certain actions like creating, updating, and deleting shifts.
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.groups.filter(name='Agency Managers').exists()
        )

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect('shifts:shift_list')


class AgencyStaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure that the user is part of the 'Agency Staff' group.
    Only Agency Staff can perform actions like booking and unbooking shifts.
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.groups.filter(name='Agency Staff').exists()
        )

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect('shifts:shift_list')


# Shift List View

class ShiftListView(LoginRequiredMixin, ListView):
    """
    Displays a list of shifts available to the user.
    - Superusers see all shifts.
    - Agency Managers and Staff see shifts within their agency.
    """
    model = Shift
    template_name = 'shifts/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        """
        Customize the queryset based on user permissions.
        """
        queryset = super().get_queryset().order_by('shift_date', 'start_time')

        if self.request.user.is_superuser:
            # Superusers can see all shifts across all agencies
            return queryset

        if hasattr(self.request.user, 'profile') and self.request.user.profile.agency:
            # Agency Managers and Staff can see shifts within their agency
            return queryset.filter(agency=self.request.user.profile.agency)

        # Users without an associated agency see no shifts
        return Shift.objects.none()


# -----------------------------------------------------------------------------------
# Shift Create View
# -----------------------------------------------------------------------------------

class ShiftCreateView(LoginRequiredMixin, AgencyManagerRequiredMixin, CreateView):
    """
    Allows Agency Managers to create new shifts within their agency.
    """
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shifts:shift_list')

    def form_valid(self, form):
        """
        Assigns the shift to the manager's agency and populates address fields based on postcode.
        """
        # Assign the shift to the manager's agency
        form.instance.agency = self.request.user.profile.agency

        # Fetch address details using the provided postcode
        postcode = form.cleaned_data.get('postcode')
        address_data = get_address_from_postcode(postcode)

        if address_data:
            form.instance.address_line1 = address_data.get('address_line1', '')
            form.instance.city = address_data.get('city', '')
            form.instance.state = address_data.get('state', '')
            form.instance.country = address_data.get('country', 'UK')
            form.instance.latitude = address_data.get('latitude')
            form.instance.longitude = address_data.get('longitude')
        else:
            messages.error(self.request, "Could not fetch address for the provided postcode.")
            return self.form_invalid(form)

        messages.success(self.request, "Shift created successfully.")
        return super().form_valid(form)



# Shift Update View

class ShiftUpdateView(LoginRequiredMixin, AgencyManagerRequiredMixin, UpdateView):
    """
    Allows Agency Managers to update existing shifts within their agency.
    """
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shifts:shift_list')

    def form_valid(self, form):
        """
        Updates address fields based on the new postcode.
        """
        # Fetch updated address details using the provided postcode
        postcode = form.cleaned_data.get('postcode')
        address_data = get_address_from_postcode(postcode)

        if address_data:
            form.instance.address_line1 = address_data.get('address_line1', '')
            form.instance.city = address_data.get('city', '')
            form.instance.state = address_data.get('state', '')
            form.instance.country = address_data.get('country', 'UK')
            form.instance.latitude = address_data.get('latitude')
            form.instance.longitude = address_data.get('longitude')
        else:
            messages.error(self.request, "Could not fetch address for the provided postcode.")
            return self.form_invalid(form)

        messages.success(self.request, "Shift updated successfully.")
        return super().form_valid(form)


# Shift Detail View

class ShiftDetailView(LoginRequiredMixin, DetailView):
    """
    Displays detailed information about a specific shift.
    """
    model = Shift
    template_name = 'shifts/shift_detail.html'
    context_object_name = 'shift'

    def get_queryset(self):
        """
        Customize the queryset based on user permissions.
        """
        queryset = super().get_queryset()

        if self.request.user.is_superuser:
            # Superusers can view all shifts
            return queryset

        if hasattr(self.request.user, 'profile') and self.request.user.profile.agency:
            # Agency Managers and Staff can view shifts within their agency
            return queryset.filter(agency=self.request.user.profile.agency)

        # Users without an associated agency see no shifts
        return Shift.objects.none()


# Shift Delete View

class ShiftDeleteView(LoginRequiredMixin, AgencyManagerRequiredMixin, DeleteView):
    """
    Allows Agency Managers to delete shifts within their agency, provided the shift is not in the past.
    """
    model = Shift
    template_name = 'shifts/shift_confirm_delete.html'
    success_url = reverse_lazy('shifts:shift_list')

    def delete(self, request, *args, **kwargs):
        """
        Overrides the delete method to add custom validation.
        """
        shift = self.get_object()

        if shift.shift_date < timezone.now().date():
            messages.error(request, "Cannot delete a past shift.")
            return HttpResponseRedirect(self.success_url)

        messages.success(request, f'Shift "{shift.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Shift Booking Function

@user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name='Agency Staff').exists())
def book_shift(request, shift_id):
    """
    Allows Agency Staff to book a shift.
    """
    shift = get_object_or_404(Shift, id=shift_id)

    # Ensure user is in the same agency as the shift
    if shift.agency != request.user.profile.agency:
        messages.error(request, "You cannot book shifts from another agency.")
        return redirect('shifts:shift_list')

    # Check if shift is in the past
    if shift.shift_date < timezone.now().date():
        messages.error(request, "You cannot book a shift that is in the past.")
        return redirect('shifts:shift_list')

    # Check if shift is fully booked
    if shift.is_full:
        messages.error(request, "This shift is already fully booked.")
        return redirect('shifts:shift_list')

    # Check if the user is already assigned to this shift
    if ShiftAssignment.objects.filter(worker=request.user, shift=shift).exists():
        messages.error(request, "You are already assigned to this shift.")
        return redirect('shifts:shift_list')

    # Book the shift
    ShiftAssignment.objects.create(worker=request.user, shift=shift)
    messages.success(request, "You have successfully booked this shift.")
    return redirect('shifts:shift_list')


# Shift Unbooking Function

@user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name='Agency Staff').exists())
def unbook_shift(request, shift_id):
    """
    Allows Agency Staff to unbook a shift they are assigned to.
    """
    shift = get_object_or_404(Shift, id=shift_id)

    # Ensure user is in the same agency as the shift
    if shift.agency != request.user.profile.agency:
        messages.error(request, "You cannot unbook shifts from another agency.")
        return redirect('shifts:shift_list')

    # Check if shift is in the past
    if shift.shift_date < timezone.now().date():
        messages.error(request, "You cannot unbook a shift that is in the past.")
        return redirect('shifts:shift_list')

    # Check if the user is assigned to this shift
    assignment = ShiftAssignment.objects.filter(worker=request.user, shift=shift).first()
    if not assignment:
        messages.error(request, "You are not assigned to this shift.")
        return redirect('shifts:shift_list')

    # Unbook the shift
    assignment.delete()
    messages.success(request, "You have successfully unbooked this shift.")
    return redirect('shifts:shift_list')


# AJAX View to Fetch Address Details Based on Postcode

@require_GET
@login_required
def get_address(request):
    """
    AJAX view to fetch address details based on a given postcode.
    Only accessible by users associated with an agency.
    """
    if not request.user.groups.filter(name__in=['Agency Managers', 'Agency Staff']).exists():
        return JsonResponse({'success': False, 'message': 'Unauthorized access.'}, status=403)
    
    postcode = request.GET.get('postcode', '').strip()
    if not postcode:
        return JsonResponse({'success': False, 'message': 'Postcode is required.'}, status=400)
    
    address = get_address_from_postcode(postcode)
    if address:
        return JsonResponse({'success': True, 'address': address})
    else:
        return JsonResponse({'success': False, 'message': 'Address not found.'}, status=404)
