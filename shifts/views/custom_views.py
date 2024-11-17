import base64
import csv
import logging
import uuid

import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Prefetch,
    Q,
    Sum,
)
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django_filters.views import FilterView

from accounts.forms import StaffCreationForm, StaffUpdateForm
from accounts.models import Agency, Profile
from core.mixins import (
    AgencyManagerRequiredMixin,
    AgencyOwnerRequiredMixin,
    AgencyStaffRequiredMixin,
    FeatureRequiredMixin,
    SubscriptionRequiredMixin,
)
from notifications.models import Notification
from shifts.filters import ShiftFilter
from shifts.forms import (
    AssignWorkerForm,
    ShiftCompletionForm,
    ShiftForm,
    StaffPerformanceForm,
    UnassignWorkerForm,
)
from shifts.models import Shift, ShiftAssignment, StaffPerformance
from shifts.utils import is_shift_full, is_user_assigned
from shiftwise.utils import generate_shift_code, haversine_distance

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
