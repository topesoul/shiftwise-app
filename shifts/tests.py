from django.test import TestCase

# tests
from django.test import TestCase
from .models import Shift

class ShiftTestCase(TestCase):
    def test_shift_creation(self):
        shift = Shift.objects.create(name="Morning Shift", start_time="08:00", end_time="12:00")
        self.assertEqual(shift.name, "Morning Shift")
