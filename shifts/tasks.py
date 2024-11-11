# /workspace/shiftwise/shifts/tasks.py

from celery import shared_task
from shiftwise.utils import auto_assign_shifts


@shared_task
def auto_assign_shifts_task():
    """
    Celery task to auto-assign shifts based on worker preferences.
    """
    auto_assign_shifts()
