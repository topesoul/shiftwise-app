# /workspace/shiftwise/shifts/tests.py

from datetime import date, time, timedelta

from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Agency, Profile, User

from .models import Shift, ShiftAssignment


class ShiftListViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create an agency
        self.agency = Agency.objects.create(
            name="Test Agency",
            postcode="SW1A1AA",
            address_line1="10 Downing Street",
            city="London",
            email="agency@test.com",
            agency_type="staffing",
        )

        # Create groups
        self.manager_group = Group.objects.create(name="Agency Managers")
        self.staff_group = Group.objects.create(name="Agency Staff")

        # Create a manager user
        self.manager_user = User.objects.create_user(
            username="manager", password="pass123"
        )
        self.manager_user.groups.add(self.manager_group)
        Profile.objects.create(user=self.manager_user, agency=self.agency)

        # Create a staff user
        self.staff_user = User.objects.create_user(username="staff", password="pass123")
        self.staff_user.groups.add(self.staff_group)
        Profile.objects.create(user=self.staff_user, agency=self.agency)

        # Create a shift
        self.shift = Shift.objects.create(
            name="Test Shift",
            shift_date=date.today() + timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            capacity=2,
            agency=self.agency,
            postcode="SW1A1AA",
            address_line1="10 Downing Street",
            city="London",
            shift_type="regular",
            hourly_rate=15.00,
            status=Shift.STATUS_PENDING,
        )

        # Create a shift assignment
        self.assignment = ShiftAssignment.objects.create(
            shift=self.shift,
            worker=self.staff_user,
            role="Staff",
            status=ShiftAssignment.CONFIRMED,
        )

    def test_shift_list_view_as_manager(self):
        self.client.login(username="manager", password="pass123")
        response = self.client.get(reverse("shifts:shift_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Shift")
        self.assertTemplateUsed(response, "shifts/shift_list.html")

    def test_shift_list_view_as_staff(self):
        self.client.login(username="staff", password="pass123")
        response = self.client.get(reverse("shifts:shift_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Shift")
        self.assertTemplateUsed(response, "shifts/shift_list.html")

    def test_shift_list_view_unauthenticated(self):
        response = self.client.get(reverse("shifts:shift_list"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_shift_assignments_in_template(self):
        self.client.login(username="manager", password="pass123")
        response = self.client.get(reverse("shifts:shift_list"))
        self.assertContains(response, self.staff_user.get_full_name())

    def test_shift_is_full_property(self):
        # Initially, capacity is 2 and one assignment exists
        self.assertFalse(self.shift.is_full)

        # Assign another worker to fill the shift
        new_staff_user = User.objects.create_user(username="staff2", password="pass123")
        new_staff_user.groups.add(self.staff_group)
        Profile.objects.create(user=new_staff_user, agency=self.agency)
        ShiftAssignment.objects.create(
            shift=self.shift,
            worker=new_staff_user,
            role="Staff",
            status=ShiftAssignment.CONFIRMED,
        )

        # Refresh from DB
        self.shift.refresh_from_db()
        self.assertTrue(self.shift.is_full)

    def test_shift_available_slots_property(self):
        # Initially, capacity is 2 and one assignment exists
        self.assertEqual(self.shift.available_slots, 1)

        # Assign another worker
        new_staff_user = User.objects.create_user(username="staff2", password="pass123")
        new_staff_user.groups.add(self.staff_group)
        Profile.objects.create(user=new_staff_user, agency=self.agency)
        ShiftAssignment.objects.create(
            shift=self.shift,
            worker=new_staff_user,
            role="Staff",
            status=ShiftAssignment.CONFIRMED,
        )

        # Refresh from DB
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.available_slots, 0)

    def test_haversine_distance_calculation(self):
        from .utils import haversine_distance

        # Coordinates for London and Paris
        distance = haversine_distance(
            51.5074, -0.1278, 48.8566, 2.3522, unit="kilometers"
        )
        self.assertAlmostEqual(distance, 343.5, delta=1.0)
