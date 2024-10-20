# shifts/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import Shift, ShiftAssignment
from .forms import ShiftForm, StaffCreationForm, StaffUpdateForm
from .mixins import SubscriptionRequiredMixin, AgencyManagerRequiredMixin
from django.db.models import Prefetch
from django.http import JsonResponse
from .utils import get_address_from_postcode
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance as DistanceFunc  # Renamed to avoid conflict
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # Distance object for specifying units

User = get_user_model()


def is_agency_manager(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Agency Managers').exists())


@login_required
@user_passes_test(is_agency_manager)
def staff_list(request):
    agency = request.user.profile.agency
    staff_members = User.objects.filter(profile__agency=agency, groups__name='Agency Staff')
    return render(request, 'shifts/staff_list.html', {'staff_members': staff_members})


@login_required
@user_passes_test(is_agency_manager)
def add_staff(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Assign the user to the 'Agency Staff' group
            agency_staff_group, created = Group.objects.get_or_create(name='Agency Staff')
            user.groups.add(agency_staff_group)
            # Associate the user with the agency
            user.profile.agency = request.user.profile.agency
            user.profile.save()
            messages.success(request, "Staff member added successfully.")
            return redirect('shifts:staff_list')
    else:
        form = StaffCreationForm()
    return render(request, 'shifts/add_staff.html', {'form': form})


@login_required
@user_passes_test(is_agency_manager)
def edit_staff(request, user_id):
    staff_member = get_object_or_404(User, id=user_id, profile__agency=request.user.profile.agency)
    if request.method == 'POST':
        form = StaffUpdateForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff member updated successfully.")
            return redirect('shifts:staff_list')
    else:
        form = StaffUpdateForm(instance=staff_member)
    return render(request, 'shifts/edit_staff.html', {'form': form, 'staff_member': staff_member})


@login_required
@user_passes_test(is_agency_manager)
def delete_staff(request, user_id):
    staff_member = get_object_or_404(User, id=user_id, profile__agency=request.user.profile.agency)
    if request.method == 'POST':
        staff_member.is_active = False
        staff_member.save()
        messages.success(request, "Staff member deactivated successfully.")
        return redirect('shifts:staff_list')
    return render(request, 'shifts/delete_staff.html', {'staff_member': staff_member})


class ShiftListView(LoginRequiredMixin, ListView):
    """
    Displays a list of shifts available to the user.
    """
    model = Shift
    template_name = 'shifts/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 10

    def get_queryset(self):
        """
        Customize the queryset based on user permissions and proximity.
        """
        user = self.request.user
        profile = user.profile

        if not profile.location:
            queryset = Shift.objects.none()
        else:
            queryset = Shift.objects.annotate(
                distance=DistanceFunc('location', profile.location, spheroid=True)
            ).filter(
                distance__lte=D(mi=profile.travel_radius)  # Changed from meters to miles
            ).order_by('shift_date', 'start_time')

            # Filter based on user role
            if user.is_superuser:
                pass  # Superusers see all shifts
            elif user.groups.filter(name='Agency Managers').exists():
                queryset = queryset.filter(agency=profile.agency)
            elif user.groups.filter(name='Agency Staff').exists():
                queryset = queryset.filter(agency=profile.agency)
            else:
                queryset = Shift.objects.none()

        # Prefetch assignments and annotate shifts
        queryset = queryset.prefetch_related(
            Prefetch(
                'assignments',
                queryset=ShiftAssignment.objects.select_related('worker')
            )
        )

        # Annotate shifts with user-specific properties
        for shift in queryset:
            shift.is_assigned = shift.assignments.filter(worker=user).exists()
            shift.can_book = (
                user.groups.filter(name='Agency Staff').exists() and
                not shift.is_full and
                not shift.is_assigned
            )
            shift.can_unbook = user.groups.filter(name='Agency Staff').exists() and shift.is_assigned
            shift.can_edit = user.is_superuser or (
                user.groups.filter(name='Agency Managers').exists() and shift.agency == profile.agency
            )
            shift.assigned_workers = shift.assignments.all()

        return queryset


class ShiftCreateView(LoginRequiredMixin, AgencyManagerRequiredMixin, CreateView):
    """
    Allows agency managers to create new shifts.
    """
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shifts:shift_list')

    def form_valid(self, form):
        shift = form.save(commit=False)
        # Ensure that the agency is set before saving
        if hasattr(self.request.user, 'profile') and self.request.user.profile.agency:
            shift.agency = self.request.user.profile.agency
        else:
            # If the user doesn't have an agency, raise an error
            messages.error(self.request, "You do not have an agency associated with your profile.")
            return redirect('shifts:shift_list')
        # Convert latitude and longitude to Point
        if shift.latitude and shift.longitude:
            shift.location = Point(float(shift.longitude), float(shift.latitude), srid=4326)
        shift.save()
        messages.success(self.request, "Shift created successfully.")
        return redirect(self.success_url)


class ShiftUpdateView(LoginRequiredMixin, AgencyManagerRequiredMixin, UpdateView):
    """
    Allows agency managers to update existing shifts.
    """
    model = Shift
    form_class = ShiftForm
    template_name = 'shifts/shift_form.html'
    success_url = reverse_lazy('shifts:shift_list')

    def get_queryset(self):
        """
        Limit shifts to those belonging to the user's agency.
        """
        return Shift.objects.filter(agency=self.request.user.profile.agency)

    def form_valid(self, form):
        messages.success(self.request, "Shift updated successfully.")
        shift = form.save(commit=False)
        # Update location if latitude and longitude are provided
        if shift.latitude and shift.longitude:
            shift.location = Point(float(shift.longitude), float(shift.latitude), srid=4326)
        shift.save()
        return super().form_valid(form)


class ShiftDeleteView(LoginRequiredMixin, AgencyManagerRequiredMixin, DeleteView):
    """
    Allows agency managers to delete shifts.
    """
    model = Shift
    template_name = 'shifts/shift_confirm_delete.html'
    success_url = reverse_lazy('shifts:shift_list')

    def get_queryset(self):
        """
        Limit shifts to those belonging to the user's agency.
        """
        return Shift.objects.filter(agency=self.request.user.profile.agency)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Shift deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ShiftDetailView(LoginRequiredMixin, DetailView):
    """
    Displays details of a specific shift.
    """
    model = Shift
    template_name = 'shifts/shift_detail.html'
    context_object_name = 'shift'

    def get_queryset(self):
        """
        Limit shifts to those accessible by the user.
        """
        user = self.request.user
        queryset = Shift.objects.select_related('agency').prefetch_related('assignments__worker')

        if user.is_superuser:
            return queryset
        elif user.groups.filter(name='Agency Managers').exists():
            return queryset.filter(agency=user.profile.agency)
        elif user.groups.filter(name='Agency Staff').exists():
            return queryset.filter(agency=user.profile.agency)
        else:
            return Shift.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = self.object
        user = self.request.user
        context['is_assigned'] = shift.assignments.filter(worker=user).exists()
        context['can_book'] = (
            user.groups.filter(name='Agency Staff').exists() and
            not shift.is_full and
            not context['is_assigned']
        )
        context['can_unbook'] = user.groups.filter(name='Agency Staff').exists() and context['is_assigned']
        context['can_edit'] = user.is_superuser or (
            user.groups.filter(name='Agency Managers').exists() and shift.agency == user.profile.agency
        )
        context['assigned_workers'] = shift.assignments.all()

        # Provide list of available workers for assignment
        if user.is_superuser or (user.groups.filter(name='Agency Managers').exists() and shift.agency == user.profile.agency):
            assigned_worker_ids = shift.assignments.values_list('worker_id', flat=True)
            context['available_workers'] = User.objects.filter(
                profile__agency=shift.agency,
                groups__name='Agency Staff',
                is_active=True
            ).exclude(id__in=assigned_worker_ids)
            # Permission to assign workers
            context['can_assign_workers'] = True
        else:
            context['can_assign_workers'] = False

        return context


@login_required
def book_shift(request, shift_id):
    """
    Allows agency staff to book a shift.
    """
    user = request.user
    shift = get_object_or_404(Shift, id=shift_id)

    if not user.groups.filter(name='Agency Staff').exists():
        messages.error(request, "You do not have permission to book shifts.")
        return redirect('shifts:shift_list')

    if shift.is_full:
        messages.error(request, "This shift is already full.")
        return redirect('shifts:shift_list')

    if ShiftAssignment.objects.filter(shift=shift, worker=user).exists():
        messages.info(request, "You have already booked this shift.")
        return redirect('shifts:shift_list')

    ShiftAssignment.objects.create(shift=shift, worker=user)
    messages.success(request, "You have successfully booked the shift.")
    return redirect('shifts:shift_list')


@login_required
def unbook_shift(request, shift_id):
    """
    Allows agency staff to unbook a shift.
    """
    user = request.user
    shift = get_object_or_404(Shift, id=shift_id)

    if not user.groups.filter(name='Agency Staff').exists():
        messages.error(request, "You do not have permission to unbook shifts.")
        return redirect('shifts:shift_list')

    assignment = ShiftAssignment.objects.filter(shift=shift, worker=user).first()
    if not assignment:
        messages.error(request, "You have not booked this shift.")
        return redirect('shifts:shift_list')

    assignment.delete()
    messages.success(request, "You have successfully unbooked the shift.")
    return redirect('shifts:shift_list')


@login_required
def get_address(request):
    """
    AJAX view to fetch address details from postcode.
    """
    postcode = request.GET.get('postcode', '')
    if postcode:
        address_data = get_address_from_postcode(postcode)
        if address_data:
            return JsonResponse({'success': True, 'address': address_data})
        else:
            return JsonResponse({'success': False, 'message': 'Address not found for the provided postcode.'})
    else:
        return JsonResponse({'success': False, 'message': 'No postcode provided.'})


class ShiftCompleteView(LoginRequiredMixin, View):
    """
    Allows staff to mark a shift as completed with a digital signature and geolocation verification.
    """

    def post(self, request, shift_id):
        shift = get_object_or_404(Shift, id=shift_id)
        user = request.user

        # Check if user is assigned to the shift
        assignment = ShiftAssignment.objects.filter(shift=shift, worker=user).first()
        if not assignment:
            return JsonResponse({'success': False, 'message': 'You are not assigned to this shift.'}, status=403)

        # Get geolocation data from the request
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not latitude or not longitude:
            return JsonResponse({'success': False, 'message': 'Geolocation data is required.'}, status=400)

        try:
            user_location = Point(float(longitude), float(latitude), srid=4326)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid geolocation data.'}, status=400)

        shift_location = shift.location

        # Transform both points to SRID 3857 (meters) for distance calculation
        user_location.transform(3857)
        shift_location.transform(3857)

        distance_meters = user_location.distance(shift_location)
        distance_miles = distance_meters / 1609.34  # Convert meters to miles

        # Define acceptable proximity in miles
        if distance_miles > 0.9:
            return JsonResponse({'success': False, 'message': 'You are not at the shift location.'}, status=403)

        # Handle signature upload
        signature = request.FILES.get('signature')
        if not signature:
            return JsonResponse({'success': False, 'message': 'Signature is required.'}, status=400)

        shift.signature = signature
        shift.is_completed = True
        shift.completion_time = timezone.now()
        shift.save()

        messages.success(request, "Shift marked as completed successfully.")
        return JsonResponse({'success': True, 'message': 'Shift completed.'})