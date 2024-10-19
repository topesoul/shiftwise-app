from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import Shift, ShiftAssignment
from .forms import ShiftForm
from .mixins import AgencyManagerRequiredMixin
from django.db.models import Prefetch
from django.http import JsonResponse
from .utils import get_address_from_postcode
from django.contrib.auth.models import User
from django.utils import timezone


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
        Customize the queryset based on user permissions.
        """
        user = self.request.user
        queryset = Shift.objects.select_related('agency').order_by('shift_date', 'start_time')

        if user.is_superuser:
            # Superusers see all shifts
            pass
        elif user.groups.filter(name='Agency Managers').exists():
            # Agency Managers see shifts within their agency
            queryset = queryset.filter(agency=user.profile.agency)
        elif user.groups.filter(name='Agency Staff').exists():
            # Agency Staff see shifts within their agency
            queryset = queryset.filter(agency=user.profile.agency)
        else:
            # Other users see no shifts
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
            shift.can_edit = user.is_superuser or user.groups.filter(name='Agency Managers').exists()
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
        messages.success(self.request, "Shift deleted successfully.")
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
        context['can_edit'] = user.is_superuser or user.groups.filter(name='Agency Managers').exists()
        context['assigned_workers'] = shift.assignments.all()

        # Provide list of available workers for assignment
        if user.is_superuser or user.groups.filter(name='Agency Managers').exists():
            assigned_worker_ids = shift.assignments.values_list('worker_id', flat=True)
            context['available_workers'] = User.objects.filter(
                profile__agency=shift.agency,
                groups__name='Agency Staff'
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
            return JsonResponse({'success': True, 'data': address_data})
        else:
            return JsonResponse({'success': False, 'message': 'Address not found for the provided postcode.'})
    else:
        return JsonResponse({'success': False, 'message': 'No postcode provided.'})


@login_required
def assign_worker(request, pk):
    """
    Allows managers to assign a worker to a shift.
    """
    shift = get_object_or_404(Shift, pk=pk)
    user = request.user

    if not (user.is_superuser or user.groups.filter(name='Agency Managers').exists()):
        messages.error(request, "You do not have permission to assign workers.")
        return redirect('shifts:shift_detail', pk=pk)

    if request.method == 'POST':
        worker_id = request.POST.get('worker_id')
        worker = get_object_or_404(User, id=worker_id)

        # Check if worker belongs to the same agency
        if worker.profile.agency != shift.agency:
            messages.error(request, "Worker does not belong to your agency.")
            return redirect('shifts:shift_detail', pk=pk)

        # Check if shift is full
        if shift.is_full:
            messages.error(request, "This shift is already full.")
            return redirect('shifts:shift_detail', pk=pk)

        # Check if worker is already assigned
        if ShiftAssignment.objects.filter(shift=shift, worker=worker).exists():
            messages.info(request, f"{worker.get_full_name()} is already assigned to this shift.")
            return redirect('shifts:shift_detail', pk=pk)

        # Assign worker
        ShiftAssignment.objects.create(shift=shift, worker=worker)
        messages.success(request, f"{worker.get_full_name()} has been assigned to the shift.")
        return redirect('shifts:shift_detail', pk=pk)
    else:
        return redirect('shifts:shift_detail', pk=pk)