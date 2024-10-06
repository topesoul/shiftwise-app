from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Shift, ShiftAssignment
from .forms import ShiftForm

class ShiftAssignmentTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username="testuser", password="password")
        
        # Create a shift
        self.shift = Shift.objects.create(
            name="Morning Shift",
            start_time="08:00",
            end_time="12:00",
            shift_date=timezone.now().date(),
            postcode="SW1A 1AA",
            address_line1="10 Downing Street",
            city="London"
        )

    def test_shift_assignment(self):
        # Assign the user to the shift
        assignment = ShiftAssignment.objects.create(worker=self.user, shift=self.shift)
        
        # Test the assignment was created
        self.assertEqual(assignment.worker.username, "testuser")
        self.assertEqual(assignment.shift.name, "Morning Shift")
        self.assertTrue(ShiftAssignment.objects.filter(worker=self.user, shift=self.shift).exists())

class ShiftTestCase(TestCase):
    def setUp(self):
        # Setup for shift creation test
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
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors}")

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

class ShiftListViewTestCase(TestCase):
    def test_shift_list_view(self):
        response = self.client.get(reverse('shift_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shifts/shift_list.html')
        self.assertContains(response, "Morning Shift")
        self.assertContains(response, "Afternoon Shift")

class AuthenticationTestCase(TestCase):
    def test_login_page(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log In")

class ShiftUpdateTestCase(TestCase):
    def setUp(self):
        # Setup for shift update test
        self.shift = Shift.objects.create(
            name="Morning Shift",
            start_time="08:00",
            end_time="12:00",
            shift_date="2024-09-30",  
            postcode="SW1A 1AA",
            address_line1="10 Downing Street",
            city="London"
        )

    def test_shift_update(self):
        response = self.client.post(reverse('shift_update', args=[self.shift.id]), {
            'name': 'Updated Shift',
            'start_time': '09:00',
            'end_time': '13:00',
            'shift_date': '2024-09-30',
            'postcode': 'SW1A 1AA',
            'address_line1': '10 Downing Street',
            'city': 'London'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        updated_shift = Shift.objects.get(id=self.shift.id)
        self.assertEqual(updated_shift.name, 'Updated Shift')

class ShiftDeleteTestCase(TestCase):
    def setUp(self):
        # Setup for shift delete test
        self.shift = Shift.objects.create(
            name="Morning Shift",
            start_time="08:00",
            end_time="12:00",
            shift_date="2024-09-30",
            postcode="SW1A 1AA",
            address_line1="10 Downing Street",
            city="London"
        )

    def test_shift_delete(self):
        response = self.client.post(reverse('shift_delete', args=[self.shift.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertFalse(Shift.objects.filter(id=self.shift.id).exists())  # Ensure the shift no longer exists
