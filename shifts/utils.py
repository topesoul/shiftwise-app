# /workspace/shiftwise/shifts/utils.py

from .models import ShiftAssignment


def is_shift_full(shift):
    return ShiftAssignment.objects.filter(shift=shift).count() >= shift.capacity


def is_user_assigned(shift, user):
    return ShiftAssignment.objects.filter(shift=shift, worker=user).exists()
