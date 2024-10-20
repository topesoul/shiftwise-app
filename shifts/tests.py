from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from .models import Shift, ShiftAssignment, Agency
from datetime import date, time, timedelta

class ShiftViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.agency = Agency.objects.create(
            name='Test Agency',
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            email='agency@test.com',
            agency_type='staffing'
        )
        # Create groups
        self.manager_group = Group.objects.create(name='Agency Managers')
        self.staff_group = Group.objects.create(name='Agency Staff')
        # Create users
        self.manager_user = User.objects.create_user(username='manager', password='pass123')
        self.manager_user.groups.add(self.manager_group)
        self.manager_user.profile.agency = self.agency
        self.manager_user.profile.save()

        self.staff_user = User.objects.create_user(username='staff', password='pass123')
        self.staff_user.groups.add(self.staff_group)
        self.staff_user.profile.agency = self.agency
        self.staff_user.profile.save()

        self.shift = Shift.objects.create(
            name='Test Shift',
            start_time=time(9, 0),
            end_time=time(17, 0),
            shift_date=date.today() + timedelta(days=1),
            capacity=2,
            agency=self.agency,
            postcode='SW1A1AA',
            address_line1='10 Downing Street',
            city='London',
            shift_type='regular',
            hourly_rate=15.00,
            status='pending'
        )

    def test_shift_list_view_as_manager(self):
        self.client.login(username='manager', password='pass123')
        response = self.client.get(reverse('shifts:shift_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Shift')
        self.assertTemplateUsed(response, 'shifts/shift_list.html')

    def test_shift_create_view_as_manager(self):
        self.client.login(username='manager', password='pass123')
        response = self.client.post(reverse('shifts:shift_create'), {
            'name': 'New Shift',
            'start_time': '08:00',
            'end_time': '16:00',
            'shift_date': (timezone.now().date() + timedelta(days=2)).isoformat(),
            'capacity': 3,
            'postcode': 'SW1A1AA',
            'address_line1': '10 Downing Street',
            'city': 'London',
            'shift_type': 'regular',
            'hourly_rate': '20.00',
            'status': 'pending'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Shift.objects.filter(name='New Shift').exists())

    def test_shift_create_view_as_staff(self):
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('shifts:shift_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_book_shift_view(self):
        self.client.login(username='staff', password='pass123')
        response = self.client.post(reverse('shifts:book_shift', args=[self.shift.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ShiftAssignment.objects.filter(worker=self.staff_user, shift=self.shift).exists())

    def test_unbook_shift_view(self):
        self.client.login(username='staff', password='pass123')
        ShiftAssignment.objects.create(worker=self.staff_user, shift=self.shift)
        response = self.client.post(reverse('shifts:unbook_shift', args=[self.shift.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ShiftAssignment.objects.filter(worker=self.staff_user, shift=self.shift).exists())

    def test_shift_list_view_as_superuser(self):
        superuser = User.objects.create_superuser(username='admin', password='adminpass')
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('shifts:shift_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Shift')

    def test_shift_list_view_unauthenticated(self):
        response = self.client.get(reverse('shifts:shift_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
