import base64
import csv
import uuid
import logging
import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.base import ContentFile
from django.db.models import Q, Count, F, Sum, FloatField, ExpressionWrapper, Prefetch
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView, View, TemplateView, FormView
)
from django_filters.views import FilterView
from accounts.models import Profile, Agency
from notifications.models import Notification
from accounts.forms import StaffCreationForm, StaffUpdateForm
from shifts.models import Shift, ShiftAssignment, StaffPerformance
from shifts.forms import ShiftForm, ShiftCompletionForm, StaffPerformanceForm, AssignWorkerForm, UnassignWorkerForm
from shifts.filters import ShiftFilter
from shifts.utils import is_shift_full, is_user_assigned
from core.mixins import AgencyOwnerRequiredMixin, SubscriptionRequiredMixin, AgencyManagerRequiredMixin, AgencyStaffRequiredMixin, FeatureRequiredMixin
from shiftwise.utils import haversine_distance,  generate_shift_code

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()
def custom_permission_denied_view(request, exception):
    """
    Render a custom 403 Forbidden page.
    """
    return render(request, "403.html", status=403)

def custom_page_not_found_view(request, exception):
    """
    Render a custom 404 Not Found page.
    """
    return render(request, "404.html", status=404)

def custom_server_error_view(request):
    """
    Render a custom 500 Server Error page.
    """
    return render(request, "500.html", status=500)
