from django.test import TestCase

# tests
from django.test import TestCase
from .models import Shift

class ShiftTestCase(TestCase):
    def test_shift_creation(self):
        shift = Shift.objects.create(name="Morning Shift", start_time="08:00", end_time="12:00")
        self.assertEqual(shift.name, "Morning Shift")

from django.urls import reverse
from .forms import ShiftForm

class ShiftFormTestCase(TestCase):
    def test_valid_shift_form(self):
        form_data = {
            'name': 'Afternoon Shift',
            'start_time': '12:00',
            'end_time': '18:00',
        }
        form = ShiftForm(data=form_data)
        self.assertTrue(form.is_valid())

class ShiftListViewTestCase(TestCase):
    def test_shift_list_view(self):
        response = self.client.get(reverse('shift_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All Shifts")