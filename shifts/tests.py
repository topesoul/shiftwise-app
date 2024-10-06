from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Shift, ShiftAssignment
from .forms import ShiftForm


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
        self.user = User.objects.create_user(username="testuser", password="password")
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
        """
        Test that a shift can be assigned to a worker, and the assignment is 
        correctly stored in the database.
        """
        assignment = ShiftAssignment.objects.create(worker=self.user, shift=self.shift)

        # Ensure the assignment is created and fields are correct
        self.assertEqual(assignment.worker.username, "testuser")
        self.assertEqual(assignment.shift.name, "Morning Shift")
        self.assertTrue(ShiftAssignment.objects.filter(worker=self.user, shift=self.shift).exists())


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
        """
        Test that a shift is created successfully and that all attributes 
        are set as expected.
        """
        self.assertEqual(self.shift.name, "Morning Shift")
        self.assertEqual(self.shift.city, "London")
        self.assertEqual(self.shift.postcode, "SW1A 1AA")


class ShiftFormTestCase(TestCase):
    """
    Test case for validating the ShiftForm, ensuring proper validation and 
    form submission behaviors.
    """

    def test_valid_shift_form(self):
        """
        Test that the form is valid when all required fields are provided 
        with appropriate values.
        """
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
        """
        Test that the form is invalid when required fields are missing 
        (e.g., shift_date is missing in this test).
        """
        form_data = {
            'name': 'Afternoon Shift',
            'start_time': '12:00',
            'end_time': '18:00',
            'postcode': 'SW1A 1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
        }
        form = ShiftForm(data=form_data)
        self.assertFalse(form.is_valid())  # Form should fail due to missing shift_date


class ShiftListViewTestCase(TestCase):
    """
    Test case for validating the behavior of the Shift List View, which lists 
    all the available shifts and renders them correctly on the page.
    """

    def setUp(self):
        """
        Set up test data for the shift list view. This includes creating 
        multiple shifts to ensure pagination and listing works as expected.
        """
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
        """
        Test that the Shift List View renders the correct template and 
        displays the created shifts in the response.
        """
        response = self.client.get(reverse('shift_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shifts/shift_list.html')
        self.assertContains(response, "Morning Shift")
        self.assertContains(response, "Afternoon Shift")


class AuthenticationTestCase(TestCase):
    """
    Test case for validating the authentication-related views, particularly 
    the login view.
    """

    def test_login_page(self):
        """
        Test that the login page renders successfully and contains the 
        expected content, such as the "Log In" button or text.
        """
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log In")


class ShiftUpdateTestCase(TestCase):
    """
    Test case for validating the update functionality of shifts, ensuring 
    that shift data can be modified and saved successfully.
    """

    def setUp(self):
        """
        Set up test data by creating an initial shift, which will be 
        updated in the subsequent test case.
        """
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
        """
        Test that an existing shift can be updated with new values and that 
        the updated data is saved correctly in the database.
        """
        response = self.client.post(reverse('shift_update', args=[self.shift.id]), {
            'name': 'Updated Shift',
            'start_time': '09:00',
            'end_time': '13:00',
            'shift_date': '2024-09-30',
            'postcode': 'SW1A 1AA',
            'address_line1': '10 Downing Street',
            'city': 'London'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after update
        updated_shift = Shift.objects.get(id=self.shift.id)
        self.assertEqual(updated_shift.name, 'Updated Shift')


class ShiftDeleteTestCase(TestCase):
    """
    Test case for ensuring shifts can be deleted and that the deletion 
    operation is handled correctly.
    """

    def setUp(self):
        """
        Set up the test by creating a shift, which will be deleted in 
        the subsequent test case.
        """
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
        """
        Test that a shift can be deleted successfully and that the deletion 
        is reflected in the database.
        """
        response = self.client.post(reverse('shift_delete', args=[self.shift.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect after deletion
        self.assertFalse(Shift.objects.filter(id=self.shift.id).exists())  # Ensure shift is deleted
