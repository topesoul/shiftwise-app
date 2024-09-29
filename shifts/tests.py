from django.test import TestCase
from django.urls import reverse
from .models import Shift
from .forms import ShiftForm
from django.utils import timezone

class ShiftTestCase(TestCase):
    def setUp(self):
        self.shift = Shift.objects.create(
            name="Morning Shift",
            start_time="08:00",
            end_time="12:00",
            shift_date="2024-09-30",  
            postcode="SW1A 1AA",
            address_line1="10 Downing Street",
            city="London"
        )

    def test_shift_creation(self):
        # Testing that the shift was created successfully
        self.assertEqual(self.shift.name, "Morning Shift")
        self.assertEqual(self.shift.city, "London")
        self.assertEqual(self.shift.postcode, "SW1A 1AA")

class ShiftFormTestCase(TestCase):
    def test_valid_shift_form(self):
        # Adding all required fields
        form_data = {
            'name': 'Afternoon Shift',
            'start_time': '12:00',
            'end_time': '18:00',
            'shift_date': '2024-09-30',
            'postcode': 'SW1A 1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
        }
        form = ShiftForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_shift_form(self):
        # Missing a required field (e.g., shift_date)
        form_data = {
            'name': 'Afternoon Shift',
            'start_time': '12:00',
            'end_time': '18:00',
            'postcode': 'SW1A 1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
        }
        form = ShiftForm(data=form_data)
        self.assertFalse(form.is_valid())  # This should fail because shift_date is missing

class ShiftListViewTestCase(TestCase):
    def setUp(self):
        # Creating some shifts to populate the view
        Shift.objects.create(
            name="Morning Shift",
            start_time="08:00",
            end_time="12:00",
            shift_date=timezone.now().date(),
            postcode="SW1A 1AA",
            address_line1="10 Downing Street",
            city="London"
        )
        Shift.objects.create(
            name="Afternoon Shift",
            start_time="12:00",
            end_time="18:00",
            shift_date=timezone.now().date(),
            postcode="SW1A 1AA",
            address_line1="10 Downing Street",
            city="London"
        )

    def test_shift_list_view(self):
        response = self.client.get(reverse('shift_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shift_list.html')
        self.assertContains(response, "Morning Shift")
        self.assertContains(response, "Afternoon Shift")

class AuthenticationTestCase(TestCase):
    def test_login_page(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log In")
