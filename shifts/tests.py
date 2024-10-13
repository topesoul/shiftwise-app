from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from .models import Shift, ShiftAssignment, Agency
from .forms import ShiftForm
from datetime import date, time, timedelta


class ShiftAssignmentTestCase(TestCase):
    """
    Test case for handling the assignment of shifts to workers.
    This ensures that workers can be correctly assigned to a shift 
    and that the relationship between shifts and workers is maintained.
    """

    def setUp(self):
        """
        Set up initial test data, including a user (worker) and a shift.
        This method is run before each test to ensure a clean test environment.
        """
        self.agency = Agency.objects.create(
            name='Test Agency',
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            email='agency@test.com',
            agency_type='staffing'
        )
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.user.profile.agency = self.agency
        self.user.profile.save()
        self.shift = Shift.objects.create(
            name='Morning Shift',
            start_time=time(8, 0),
            end_time=time(12, 0),
            shift_date=date.today() + timedelta(days=1),
            capacity=5,
            agency=self.agency,
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            shift_type='regular',
            hourly_rate=15.00,
            status='pending'
        )

    def test_shift_assignment(self):
        """
        Test that a shift can be assigned to a worker, and the assignment is 
        correctly stored in the database.
        """
        assignment = ShiftAssignment.objects.create(worker=self.user, shift=self.shift)
        self.assertEqual(assignment.worker.username, 'testuser')
        self.assertEqual(assignment.shift.name, 'Morning Shift')
        self.assertTrue(ShiftAssignment.objects.filter(worker=self.user, shift=self.shift).exists())

    def test_shift_capacity(self):
        """
        Test that the shift's available slots decrease as assignments are made.
        """
        for i in range(5):
            user = User.objects.create_user(username=f'user{i}', password='password123')
            user.profile.agency = self.agency
            user.profile.save()
            ShiftAssignment.objects.create(worker=user, shift=self.shift)
        self.assertTrue(self.shift.is_full)
        self.assertEqual(self.shift.available_slots, 0)

    def test_shift_overbooking(self):
        """
        Test that assigning a shift beyond its capacity raises a ValidationError.
        """
        for i in range(5):
            user = User.objects.create_user(username=f'user{i}', password='password123')
            user.profile.agency = self.agency
            user.profile.save()
            ShiftAssignment.objects.create(worker=user, shift=self.shift)
        with self.assertRaises(Exception):
            ShiftAssignment.objects.create(worker=self.user, shift=self.shift)


class ShiftTestCase(TestCase):
    """
    Test case for Shift model operations, specifically for ensuring shifts 
    are created correctly with all required attributes.
    """

    def setUp(self):
        """
        Set up initial test data for shift creation. This ensures each test runs 
        with fresh data, avoiding dependencies between tests.
        """
        self.agency = Agency.objects.create(
            name='Test Agency',
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            email='agency@test.com',
            agency_type='staffing'
        )
        self.shift = Shift.objects.create(
            name='Morning Shift',
            start_time=time(8, 0),
            end_time=time(12, 0),
            shift_date=date.today() + timedelta(days=1),
            capacity=5,
            agency=self.agency,
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            shift_type='regular',
            hourly_rate=15.00,
            status='pending'
        )

    def test_shift_creation(self):
        """
        Test that a shift is created successfully and that all attributes 
        are set as expected.
        """
        self.assertEqual(self.shift.name, 'Morning Shift')
        self.assertEqual(self.shift.city, 'London')
        self.assertEqual(self.shift.postcode, 'SW1A1AA')
        self.assertEqual(self.shift.agency, self.agency)

    def test_shift_str(self):
        """
        Test the string representation of the Shift model.
        """
        self.assertEqual(str(self.shift), f"{self.shift.name} on {self.shift.shift_date} for {self.agency.name}")

    def test_shift_duration(self):
        """
        Test that the shift duration is correctly calculated.
        """
        self.shift.clean()
        self.assertEqual(self.shift.duration, 4.0)

    def test_shift_past_date_validation(self):
        """
        Test that creating a shift with a past date raises a ValidationError.
        """
        past_shift = Shift(
            name='Past Shift',
            start_time=time(8, 0),
            end_time=time(12, 0),
            shift_date=date.today() - timedelta(days=1),
            capacity=5,
            agency=self.agency,
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            shift_type='regular',
            hourly_rate=15.00,
            status='pending'
        )
        with self.assertRaises(ValidationError):
            past_shift.clean()


class ShiftFormTestCase(TestCase):
    """
    Test case for validating the ShiftForm, ensuring proper validation and 
    form submission behaviors.
    """

    def setUp(self):
        self.agency = Agency.objects.create(
            name='Test Agency',
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            email='agency@test.com',
            agency_type='staffing'
        )

    def test_valid_shift_form(self):
        """
        Test that the form is valid when all required fields are provided 
        with appropriate values.
        """
        form_data = {
            'name': 'Afternoon Shift',
            'start_time': '12:00',
            'end_time': '18:00',
            'shift_date': (timezone.now().date() + timedelta(days=2)).isoformat(),
            'capacity': 3,
            'postcode': 'SW1A1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
            'shift_type': 'overtime',
            'hourly_rate': '20.00',
            'notes': 'Evening duties'
        }
        form = ShiftForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors}")

    def test_invalid_shift_form_missing_fields(self):
        """
        Test that the form is invalid when required fields are missing 
        (e.g., shift_date is missing in this test).
        """
        form_data = {
            'name': 'Afternoon Shift',
            'start_time': '12:00',
            'end_time': '18:00',
            'capacity': 3,
            'postcode': 'SW1A1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
            'shift_type': 'overtime',
            'hourly_rate': '20.00',
            'notes': 'Evening duties'
        }
        form = ShiftForm(data=form_data)
        self.assertFalse(form.is_valid())  # Form should fail due to missing shift_date
        self.assertIn('shift_date', form.errors)

    def test_invalid_shift_form_end_time_before_start_time(self):
        """
        Test that the form is invalid when end time is before start time without spanning to the next day.
        """
        form_data = {
            'name': 'Night Shift',
            'start_time': '22:00',
            'end_time': '06:00',
            'shift_date': (timezone.now().date() + timedelta(days=2)).isoformat(),
            'capacity': 3,
            'postcode': 'SW1A1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
            'shift_type': 'holiday',
            'hourly_rate': '25.00',
            'notes': 'Overnight duties'
        }
        form = ShiftForm(data=form_data)
        self.assertFalse(form.is_valid())  # Should be valid if spans to next day, adjust if needed

    def test_shift_name_validation(self):
        """
        Test that the form is invalid when the shift name contains non-alphabetic characters.
        """
        form_data = {
            'name': 'Shift123',
            'start_time': '08:00',
            'end_time': '12:00',
            'shift_date': (timezone.now().date() + timedelta(days=2)).isoformat(),
            'capacity': 3,
            'postcode': 'SW1A1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
            'shift_type': 'regular',
            'hourly_rate': '15.00',
            'notes': 'Morning duties'
        }
        form = ShiftForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)