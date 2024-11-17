# /workspace/shiftwise/shifts/filters.py

import django_filters
from django import forms
from django.db.models import Q

from .models import Shift


class ShiftFilter(django_filters.FilterSet):
    """
    FilterSet for Shift model to enable filtering by search terms, status, and date range.
    """

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search by name, agency, or shift type",
            }
        ),
    )
    status = django_filters.ChoiceFilter(
        choices=Shift.STATUS_CHOICES,
        label="Status",
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )
    shift_date_after = django_filters.DateFilter(
        field_name="shift_date",
        lookup_expr="gte",
        label="Date From",
        widget=forms.DateInput(
            attrs={
                "class": "form-control datepicker",
                "placeholder": "YYYY-MM-DD",
                "autocomplete": "off",
            }
        ),
    )
    shift_date_before = django_filters.DateFilter(
        field_name="shift_date",
        lookup_expr="lte",
        label="Date To",
        widget=forms.DateInput(
            attrs={
                "class": "form-control datepicker",
                "placeholder": "YYYY-MM-DD",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = Shift
        fields = ["status", "shift_date_after", "shift_date_before", "search"]

    def filter_search(self, queryset, name, value):
        """
        Custom filter method to search across multiple fields.
        """
        return queryset.filter(
            Q(name__icontains=value)
            | Q(agency__name__icontains=value)
            | Q(shift_type__icontains=value)
        )
